package main

import (
	"context"
	"database/sql"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"emqx-monitor/internal/config"
	"emqx-monitor/internal/monitor"
	"emqx-monitor/internal/server"
)

const version = "1.0.0"

func main() {
	// 初始化日志
	logger := log.New(os.Stdout, "emqx-monitor: ", log.LstdFlags|log.Lshortfile)

	// 加载配置
	cfg, err := config.LoadConfig("config/config.yaml")
	if err != nil {
		logger.Fatalf("Failed to load config: %v", err)
	}

	// 初始化数据库连接
	db, err := sql.Open(cfg.Database.Driver, cfg.Database.DSN)
	if err != nil {
		logger.Fatalf("Failed to connect to database: %v", err)
	}
	defer db.Close()

	// 验证数据库连接
	if err := db.Ping(); err != nil {
		logger.Fatalf("Failed to ping database: %v", err)
	}

	// 创建监控器
	monitor := monitor.New(db, cfg, logger)

	// 创建HTTP服务器
	mux := http.NewServeMux()
	mux.Handle("/health", server.HealthHandler(version))

	srv := server.New(cfg.Server.Address, mux, logger)

	// 创建上下文用于优雅关闭
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// 启动监控
	go monitor.Run(ctx)

	// 启动HTTP服务器
	go func() {
		if err := srv.Start(); err != nil && err != http.ErrServerClosed {
			logger.Fatalf("HTTP server error: %v", err)
		}
	}()

	// 等待中断信号
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	logger.Println("Shutting down server...")

	// 优雅关闭
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), cfg.Server.ShutdownTimeout)
	defer shutdownCancel()

	if err := srv.Stop(shutdownCtx); err != nil {
		logger.Printf("HTTP server shutdown error: %v", err)
	}

	logger.Println("Server exited properly")
}
