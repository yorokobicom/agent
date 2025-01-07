package logging

import (
	"testing"
)

func TestLogger(t *testing.T) {
	tests := []struct {
		name     string
		level    string
		logFunc  func(logger *MockLogger)
		expected []LogEntry
	}{
		{
			name:  "info logging",
			level: "info",
			logFunc: func(logger *MockLogger) {
				logger.Info("test message")
			},
			expected: []LogEntry{
				{Level: "INFO", Message: "test message"},
			},
		},
		{
			name:  "error logging",
			level: "info",
			logFunc: func(logger *MockLogger) {
				logger.Errorf("error: %s", "test error")
			},
			expected: []LogEntry{
				{Level: "ERROR", Message: "error: test error"},
			},
		},
		{
			name:  "multiple logs",
			level: "info",
			logFunc: func(logger *MockLogger) {
				logger.Info("first message")
				logger.Errorf("error: %s", "something broke")
				logger.Info("third message")
			},
			expected: []LogEntry{
				{Level: "INFO", Message: "first message"},
				{Level: "ERROR", Message: "error: something broke"},
				{Level: "INFO", Message: "third message"},
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			logger := NewMockLogger()
			tt.logFunc(logger)

			logs := logger.GetLogs()
			if len(logs) != len(tt.expected) {
				t.Errorf("expected %d logs, got %d", len(tt.expected), len(logs))
				return
			}

			for i, expected := range tt.expected {
				if logs[i].Level != expected.Level || logs[i].Message != expected.Message {
					t.Errorf("log entry %d mismatch:\nexpected: %+v\ngot: %+v",
						i, expected, logs[i])
				}
			}
		})
	}
}

func TestSimpleLogger(t *testing.T) {
	logger := NewLogger(&Config{Level: "info"})
	if logger == nil {
		t.Error("NewLogger returned nil")
	}

	// We can't easily test Fatalf as it calls os.Exit
	// We can't easily test actual output as it goes to stdout/stderr
	// Consider using a buffer for testing actual output in a future enhancement
}
