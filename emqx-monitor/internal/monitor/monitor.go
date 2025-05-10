package monitor

import (
	"context"
	"crypto/tls"
	"database/sql"
	"emqx-monitor/internal/config"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"sync"
	"time"

	"gopkg.in/gomail.v2"
)

type EMQXNode struct {
	ID        int       `json:"id"`
	NodeName  string    `json:"node_name"`
	PublicIP  string    `json:"public_ip"`
	IsActive  bool      `json:"is_active"`
	LastCheck time.Time `json:"last_check"`
}

type Monitor struct {
	db                  *sql.DB
	httpClient          *http.Client
	config              *config.Config // 使用 config 包中的 Config
	logger              *log.Logger
	lastNotificationMap map[string]time.Time // 保存每个节点的上次通知时间
}

func New(db *sql.DB, cfg *config.Config, logger *log.Logger) *Monitor {
	httpClient := &http.Client{
		Timeout: cfg.Monitor.HTTPTimeout,
	}

	return &Monitor{
		db:         db,
		httpClient: httpClient,
		config:     cfg,
		logger:     logger,
	}
}

func (m *Monitor) Run(ctx context.Context) {
	ticker := time.NewTicker(m.config.Monitor.CheckInterval)
	defer ticker.Stop()

	// 每6小时执行一次清理操作
	cleanTicker := time.NewTicker(6 * time.Hour)
	defer cleanTicker.Stop()

	// 初始立即运行一次
	m.checkAllNodes()

	for {
		select {
		case <-ticker.C:
			m.checkAllNodes()
		case <-cleanTicker.C:
			m.cleanOldNotifications() // 每6小时清理一次
		case <-ctx.Done():
			m.logger.Println("Monitor stopped")
			return
		}
	}
}

func (m *Monitor) checkAllNodes() {
	nodes, err := m.getNodes()
	if err != nil {
		m.logger.Printf("Error getting nodes: %v", err)
		return
	}

	var wg sync.WaitGroup
	for i := range nodes {
		wg.Add(1)
		go func(n *EMQXNode) {
			defer wg.Done()
			m.checkNodeStatus(n)
		}(&nodes[i])
	}
	wg.Wait()
}

func (m *Monitor) cleanOldNotifications() {
	now := time.Now().UTC()
	for nodeID, lastNotificationTime := range m.lastNotificationMap {
		// 如果距离上次通知超过一定时间，，则删除该记录
		if now.Sub(lastNotificationTime) > 1*time.Hour { // 1小时
			delete(m.lastNotificationMap, nodeID)
		}
	}
}

func (m *Monitor) getNodes() ([]EMQXNode, error) {
	rows, err := m.db.Query("SELECT id, node_name, node_public_ip FROM public_emqx_node")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var nodes []EMQXNode
	for rows.Next() {
		var node EMQXNode
		if err := rows.Scan(&node.ID, &node.NodeName, &node.PublicIP); err != nil {
			return nil, err
		}
		nodes = append(nodes, node)
	}

	return nodes, nil
}

func (m *Monitor) checkNodeStatus(node *EMQXNode) {
	url := fmt.Sprintf("http://%s:%d%s", node.PublicIP, m.config.Monitor.Port, m.config.Monitor.StatusEndpoint)
	isActive := false

	// 尝试 3 次检测节点是否活跃
	for i := 0; i < 3; i++ {
		resp, err := m.httpClient.Get(url)
		if err == nil {
			defer resp.Body.Close()
			if resp.StatusCode == http.StatusOK {
				_, err = io.ReadAll(resp.Body)
				if err == nil {
					isActive = true
					break
				}
			}
		}
		time.Sleep(300 * time.Millisecond)
	}

	m.logger.Printf("Checked node %s status. Active: %v", node.NodeName, isActive)

	// 如果节点是活动的，就不需要发送邮件
	if isActive {
		return
	}

	// 如果节点不活跃，检查是否需要发送通知
	now := time.Now().UTC()
	minInterval := 30 * time.Minute
	if m.lastNotificationMap == nil {
		m.lastNotificationMap = make(map[string]time.Time)
	}
	if lastNotificationTime, ok := m.lastNotificationMap[node.NodeName]; ok {
		if now.Sub(lastNotificationTime) < minInterval {
			m.logger.Printf("Skipping notification for node %s as the last notification was too recent.", node.NodeName)
			return
		}
	}

	// 发送节点宕机通知
	m.handleNodeDown(node)

	// 更新节点的最后通知时间
	m.lastNotificationMap[node.NodeName] = now
}

func (m *Monitor) handleNodeDown(node *EMQXNode) {
	payload := map[string]interface{}{
		"node_id":   node.ID,
		"node_name": node.NodeName,
		"public_ip": node.PublicIP,
		"timestamp": time.Now().UTC(),
		"message":   fmt.Sprintf("EMQX node %s (%s) is not responding", node.NodeName, node.PublicIP),
	}

	// 将 payload 转换为 JSON 格式
	jsonData, err := json.Marshal(payload)
	if err != nil {
		m.logger.Printf("Error marshaling notification payload: %v", err)
		return
	}

	// 邮件配置
	smtpHost := "smtp.qq.com"
	smtpPort := 465
	from := "2504525465@qq.com"
	// QQ 邮箱的授权码 password := ""
	// 带重试的通知发送
	to := "2504525465@qq.com"

	// 创建邮件内容
	subject := "EMQX Node Down Alert"
	body := fmt.Sprintf("Node ID: %d\nNode Name: %s\nPublic IP: %s\nTimestamp: %s\nMessage: %s",
		node.ID, node.NodeName, node.PublicIP, time.Now().UTC().String(), string(jsonData))

	// 带重试的邮件发送
	for i := 0; i < m.config.Notification.RetryCount; i++ {
		if i > 0 {
			time.Sleep(m.config.Notification.RetryInterval)
			m.logger.Printf("Retrying notification for node %s (attempt %d/%d)",
				node.NodeName, i+1, m.config.Notification.RetryCount)
		}

		// 创建新的邮件消息
		msg := gomail.NewMessage()
		msg.SetHeader("From", from)
		msg.SetHeader("To", to)
		msg.SetHeader("Subject", subject)
		msg.SetBody("text/plain", body)

		// 配置带TLS的拨号器
		d := gomail.NewDialer(smtpHost, smtpPort, from, password)
		d.TLSConfig = &tls.Config{
			ServerName: smtpHost,         // 重要：验证服务器证书
			MinVersion: tls.VersionTLS12, // 强制使用TLS 1.2+
		}

		// 发送邮件
		if err := d.DialAndSend(msg); err == nil {
			m.logger.Printf("Notification sent for node %s", node.NodeName)
			return
		} else {
			m.logger.Printf("Failed to send notification for node %s (attempt %d/%d). Error: %v",
				node.NodeName, i+1, m.config.Notification.RetryCount, err)
		}
	}

	m.logger.Printf("Failed to send notification for node %s after %d retries",
		node.NodeName, m.config.Notification.RetryCount)
}
