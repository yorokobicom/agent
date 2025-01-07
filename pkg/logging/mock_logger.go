package logging

import (
	"fmt"
	"sync"
)

// MockLogger implements Logger interface for testing
type MockLogger struct {
	mu         sync.Mutex
	logs       []LogEntry
	FatalfFunc func(format string, args ...interface{})
}

type LogEntry struct {
	Level   string
	Message string
}

func NewMockLogger() *MockLogger {
	return &MockLogger{
		logs: make([]LogEntry, 0),
	}
}

func (m *MockLogger) Info(args ...interface{}) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.logs = append(m.logs, LogEntry{
		Level:   "INFO",
		Message: fmt.Sprint(args...),
	})
}

func (m *MockLogger) Errorf(format string, args ...interface{}) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.logs = append(m.logs, LogEntry{
		Level:   "ERROR",
		Message: fmt.Sprintf(format, args...),
	})
}

func (m *MockLogger) Fatalf(format string, args ...interface{}) {
	if m.FatalfFunc != nil {
		m.FatalfFunc(format, args...)
		return
	}
	m.mu.Lock()
	defer m.mu.Unlock()
	m.logs = append(m.logs, LogEntry{
		Level:   "FATAL",
		Message: fmt.Sprintf(format, args...),
	})
}

func (m *MockLogger) GetLogs() []LogEntry {
	m.mu.Lock()
	defer m.mu.Unlock()
	return append([]LogEntry{}, m.logs...)
}

func (m *MockLogger) Clear() {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.logs = make([]LogEntry, 0)
}
