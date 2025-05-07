package server

import (
	"context"
	"log"
	"net/http"
)

type Server struct {
	httpServer *http.Server
	logger     *log.Logger
}

func New(addr string, handler http.Handler, logger *log.Logger) *Server {
	return &Server{
		httpServer: &http.Server{
			Addr:    addr,
			Handler: handler,
		},
		logger: logger,
	}
}

func (s *Server) Start() error {
	s.logger.Printf("Starting HTTP server on %s", s.httpServer.Addr)
	return s.httpServer.ListenAndServe()
}

func (s *Server) Stop(ctx context.Context) error {
	s.logger.Println("Shutting down HTTP server...")
	return s.httpServer.Shutdown(ctx)
}
