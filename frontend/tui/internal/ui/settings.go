package ui

import (
	"autobiz/internal/api"
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
)

type settingsScreen int

const (
	settingsOverview settingsScreen = iota
	settingsEditProvider
	settingsEditAPIKey
	settingsTestResult
)

type SettingsModel struct {
	client    *api.Client
	screen    settingsScreen
	status    *api.IntegrationStatus
	env       *api.EnvConfig
	testRes   *api.TestLLMResult
	testing   bool
	errMsg    string
	editBuf   string
	editField string
}

func NewSettingsModel(client *api.Client) SettingsModel {
	return SettingsModel{client: client}
}

func (m SettingsModel) Init() tea.Cmd {
	return tea.Batch(
		m.fetchStatusCmd(),
		m.fetchEnvCmd(),
	)
}

type StatusLoadedMsg struct{ Status *api.IntegrationStatus }
type EnvLoadedMsg struct{ Env *api.EnvConfig }
type TestDoneMsg struct{ Result *api.TestLLMResult }
type SettingsErrMsg struct{ Err string }

func (m SettingsModel) fetchStatusCmd() tea.Cmd {
	return func() tea.Msg {
		s, err := m.client.GetStatus()
		if err != nil {
			return SettingsErrMsg{Err: err.Error()}
		}
		return StatusLoadedMsg{Status: s}
	}
}

func (m SettingsModel) fetchEnvCmd() tea.Cmd {
	return func() tea.Msg {
		e, err := m.client.GetEnv()
		if err != nil {
			return SettingsErrMsg{Err: err.Error()}
		}
		return EnvLoadedMsg{Env: e}
	}
}

func (m SettingsModel) testLLMCmd() tea.Cmd {
	m.testing = true
	return func() tea.Msg {
		r, err := m.client.TestLLM("", "", "", "")
		if err != nil {
			return TestDoneMsg{Result: &api.TestLLMResult{Success: false, Error: err.Error()}}
		}
		return TestDoneMsg{Result: r}
	}
}

func (m SettingsModel) Update(msg tea.Msg) (SettingsModel, tea.Cmd) {
	switch msg := msg.(type) {
	case StatusLoadedMsg:
		m.status = msg.Status
	case EnvLoadedMsg:
		m.env = msg.Env
	case TestDoneMsg:
		m.testRes = msg.Result
		m.testing = false
		m.screen = settingsTestResult
	case SettingsErrMsg:
		m.errMsg = msg.Err

	case tea.KeyMsg:
		m.errMsg = ""
		switch m.screen {
		case settingsOverview:
			switch msg.String() {
			case "t":
				return m, m.testLLMCmd()
			case "R":
				return m, tea.Batch(m.fetchStatusCmd(), m.fetchEnvCmd())
			}
		case settingsTestResult:
			if msg.String() == "esc" || msg.String() == "enter" {
				m.screen = settingsOverview
				m.testRes = nil
			}
		}
	}
	return m, nil
}

func statusDot(s string) string {
	switch s {
	case "ok", "connected", "configured":
		return StyleSuccess.Render("●")
	case "error", "missing_api_key":
		return StyleError.Render("●")
	default:
		return StyleMuted.Render("○")
	}
}

func statusLabel(s string) string {
	switch s {
	case "ok", "connected", "configured":
		return StyleSuccess.Render(s)
	case "error":
		return StyleError.Render(s)
	case "missing_api_key":
		return StyleWarn.Render("missing key")
	default:
		return StyleMuted.Render(s)
	}
}

func (m SettingsModel) View() string {
	var sb strings.Builder

	sb.WriteString(StyleTitle.Render("Settings & Integrations"))
	sb.WriteString("\n\n")

	// ── Integration Status ──
	sb.WriteString(StyleInfo.Render("Integration Status"))
	sb.WriteString("\n")

	if m.status != nil {
		rows := []struct {
			name   string
			status string
			extra  string
		}{
			{"Backend", m.status.Backend.Status, ""},
			{"Database", m.status.Database.Status, m.status.Database.URL},
			{"LLM", m.status.LLM.Status, m.status.LLM.Provider + " · " + m.status.LLM.Model},
			{"Redis", m.status.Redis.Status, ""},
		}
		for _, r := range rows {
			line := fmt.Sprintf("  %s  %s", statusDot(r.status), StyleNormal.Render(r.name))
			line += fmt.Sprintf("  %s", statusLabel(r.status))
			if r.extra != "" {
				line += StyleDim.Render("  (" + r.extra + ")")
			}
			sb.WriteString(line + "\n")
		}
	} else {
		sb.WriteString(StyleMuted.Render("  Loading status...") + "\n")
	}

	sb.WriteString("\n")

	// ── LLM Provider Info ──
	if m.status != nil && m.status.LLM.Status != "" {
		sb.WriteString(StyleInfo.Render("AI Provider"))
		sb.WriteString("\n")
		sb.WriteString(fmt.Sprintf("  %s  %s\n", StyleNormal.Render("Provider:"), StyleHighlight.Render(m.status.LLM.Provider)))
		sb.WriteString(fmt.Sprintf("  %s  %s\n", StyleNormal.Render("Model:"), m.status.LLM.Model))

		status := m.status.LLM.Status
		note := m.status.LLM.Note
		if status == "configured" {
			sb.WriteString(fmt.Sprintf("  %s  %s\n\n", StyleSuccess.Render("✓ Ready"), StyleDim.Render(note)))
		} else if status == "missing_api_key" {
			sb.WriteString(fmt.Sprintf("  %s  %s\n\n", StyleWarn.Render("⚠ API key missing"), StyleDim.Render("Set in .env or use Ollama")))
		} else {
			sb.WriteString(fmt.Sprintf("  %s  %s\n\n", StyleMuted.Render("○ Not configured"), StyleDim.Render("Set LLM_PROVIDER in .env")))
		}
	}

	// ── .env Config Summary ──
	if m.env != nil && len(m.env.Env) > 0 {
		sb.WriteString(StyleInfo.Render("Configuration"))
		sb.WriteString("\n")
		for key, val := range m.env.Env {
			displayKey := StyleMuted.Render(key + ":")
			sb.WriteString(fmt.Sprintf("  %s  %s\n", displayKey, val))
		}
		sb.WriteString("\n")
	} else if m.env != nil {
		sb.WriteString(StyleWarn.Render("  ⚠ No .env file found") + "\n\n")
	}

	if m.errMsg != "" {
		sb.WriteString(StyleError.Render("✗ "+m.errMsg) + "\n\n")
	}

	sb.WriteString(StyleDim.Render("t test LLM  ·  R refresh  ·  1-5 tabs"))
	return sb.String()
}
