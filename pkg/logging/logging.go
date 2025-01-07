package logging

import (
    "fmt"
    "os"
)

type Config struct {
    Level string
}

type Logger interface {
    Info(args ...interface{})
    Errorf(format string, args ...interface{})
    Fatalf(format string, args ...interface{})
}

type simpleLogger struct {
    config *Config
}

func NewLogger(config *Config) Logger {
    return &simpleLogger{config: config}
}

func (l *simpleLogger) Info(args ...interface{}) {
    fmt.Println("[INFO]", fmt.Sprint(args...))
}

func (l *simpleLogger) Errorf(format string, args ...interface{}) {
    fmt.Printf("[ERROR] "+format+"\n", args...)
}

func (l *simpleLogger) Fatalf(format string, args ...interface{}) {
    fmt.Printf("[FATAL] "+format+"\n", args...)
    os.Exit(1)
} 