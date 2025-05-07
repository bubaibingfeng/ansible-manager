package monitor

import (
	"bytes"
	"context"
	"database/sql"
	"emqx-monitor/internal/config"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"time"
)

type EMQXNode struct {
	ID        int       `json:"id"`
	NodeName  string    `json:"node_name"`
	PublicIP  string    `json:"public_ip"`
	IsActive  bool      `json:"is_active"`
	LastCheck time.Time `json:"last_check"`
}

type Monitor struct {
	db         *sql.DB
	httpClient *http.Client
	config     *config.Config // 使用 config 包中的 Config
	logger     *log.Logger
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

	// 初始立即运行一次
	m.checkAllNodes()

	for {
		select {
		case <-ticker.C:
			m.checkAllNodes()
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

	for _, node := range nodes {
		m.checkNodeStatus(node)
	}
}

func (m *Monitor) getNodes() ([]EMQXNode, error) {
	rows, err := m.db.Query("SELECT id, node_name, public_ip, is_active, last_check FROM EMQX_Node")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var nodes []EMQXNode
	for rows.Next() {
		var node EMQXNode
		if err := rows.Scan(&node.ID, &node.NodeName, &node.PublicIP, &node.IsActive, &node.LastCheck); err != nil {
			return nil, err
		}
		nodes = append(nodes, node)
	}

	return nodes, nil
}

func (m *Monitor) checkNodeStatus(node EMQXNode) {
	url := fmt.Sprintf("http://%s%s", node.PublicIP, m.config.Monitor.StatusEndpoint)
	isActive := false

	resp, err := m.httpClient.Get(url)
	if err == nil {
		defer resp.Body.Close()
		if resp.StatusCode == http.StatusOK {
			_, err = ioutil.ReadAll(resp.Body)
			isActive = err == nil
		}
	}

	// 如果状态变化，处理通知
	if node.IsActive && !isActive {
		m.handleNodeDown(node)
	}

	// 更新数据库状态
	if err := m.updateNodeStatus(node, isActive); err != nil {
		m.logger.Printf("Error updating node %s status: %v", node.NodeName, err)
	}
}

func (m *Monitor) handleNodeDown(node EMQXNode) {
	payload := map[string]interface{}{
		"node_id":   node.ID,
		"node_name": node.NodeName,
		"public_ip": node.PublicIP,
		"timestamp": time.Now().UTC(),
		"message":   fmt.Sprintf("EMQX node %s (%s) is not responding", node.NodeName, node.PublicIP),
	}

	jsonData, err := json.Marshal(payload)
	if err != nil {
		m.logger.Printf("Error marshaling notification payload: %v", err)
		return
	}

	// 带重试的通知发送
	for i := 0; i < m.config.Notification.RetryCount; i++ {
		if i > 0 {
			time.Sleep(m.config.Notification.RetryInterval)
		}

		resp, err := m.httpClient.Post(
			m.config.Notification.WebhookURL,
			"application/json",
			bytes.NewReader(jsonData),
		)
		if err == nil {
			defer resp.Body.Close()
			if resp.StatusCode == http.StatusOK {
				m.logger.Printf("Notification sent for node %s", node.NodeName)
				return
			}
		}
	}

	m.logger.Printf("Failed to send notification for node %s after %d retries",
		node.NodeName, m.config.Notification.RetryCount)
}

func (m *Monitor) updateNodeStatus(node EMQXNode, isActive bool) error {
	_, err := m.db.Exec(
		"UPDATE EMQX_Node SET is_active = ?, last_check = ? WHERE id = ?",
		isActive, time.Now().UTC(), node.ID,
	)
	return err
}
