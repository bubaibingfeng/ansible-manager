package config

import (
	"os"
	"time"

	"gopkg.in/yaml.v2"
)

type Config struct {
	Database     DatabaseConfig `yaml:"database"`
	Monitor      MonitorConfig  `yaml:"monitor"`
	Notification NotifyConfig   `yaml:"notification"`
	Server       ServerConfig   `yaml:"server"`
}

type DatabaseConfig struct {
	Driver string `yaml:"driver"`
	DSN    string `yaml:"dsn"`
}

type MonitorConfig struct {
	CheckInterval  time.Duration `yaml:"check_interval"`
	StatusEndpoint string        `yaml:"status_endpoint"`
	HTTPTimeout    time.Duration `yaml:"http_timeout"`
}

type NotifyConfig struct {
	WebhookURL    string        `yaml:"webhook_url"`
	RetryCount    int           `yaml:"retry_count"`
	RetryInterval time.Duration `yaml:"retry_interval"`
}

type ServerConfig struct {
	Address         string        `yaml:"address"`
	ReadTimeout     time.Duration `yaml:"read_timeout"`
	WriteTimeout    time.Duration `yaml:"write_timeout"`
	ShutdownTimeout time.Duration `yaml:"shutdown_timeout"`
}

func LoadConfig(path string) (*Config, error) {
	config := &Config{}

	file, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	d := yaml.NewDecoder(file)
	if err := d.Decode(&config); err != nil {
		return nil, err
	}

	return config, nil
}
