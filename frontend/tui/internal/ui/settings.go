package ui

import (
	"autobiz/internal/api"
	"fmt"
	"sort"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
)

type SettingsModel struct {
	client      *api.Client
	status      *api.IntegrationStatus
	env         *api.EnvConfig
	testRes     *api.TestLLMResult
	testing     bool
	saving      bool
	editingKey  string
	editBuf     string
	cursorGroup int
	cursorKey   int
	errMsg      string
	successMsg  string
}

func NewSettingsModel(client *api.Client) SettingsModel {
	return SettingsModel{client: client}
}

func (m SettingsModel) Init() tea.Cmd {
	return tea.Batch(m.fetchStatusCmd(), m.fetchEnvCmd())
}

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

func (m SettingsModel) saveCmd() tea.Cmd {
	m.saving = true
	return func() tea.Msg {
		if m.env == nil || m.env.Flat == nil {
			return SavedMsg{Err: "no config loaded"}
		}
		err := m.client.SaveEnv(m.env.Flat)
		if err != nil {
			return SavedMsg{Err: err.Error()}
		}
		return SavedMsg{Ok: true}
	}
}

type StatusLoadedMsg struct{ Status *api.IntegrationStatus }
type EnvLoadedMsg struct{ Env *api.EnvConfig }
type TestDoneMsg struct{ Result *api.TestLLMResult }
type SavedMsg struct{ Ok bool; Err string }
type SettingsErrMsg struct{ Err string }

func (m SettingsModel) Update(msg tea.Msg) (SettingsModel, tea.Cmd) {
	switch msg := msg.(type) {
	case StatusLoadedMsg:
		m.status = msg.Status
	case EnvLoadedMsg:
		m.env = msg.Env
	case TestDoneMsg:
		m.testRes = msg.Result
		m.testing = false
	case SavedMsg:
		m.saving = false
		if msg.Err != "" {
			m.errMsg = msg.Err
		} else {
			m.successMsg = "✓ Settings saved to .env"
		}
	case SettingsErrMsg:
		m.errMsg = msg.Err

	case tea.KeyMsg:
		m.errMsg = ""
		m.successMsg = ""

		if m.editingKey != "" {
			return m.handleEdit(msg)
		}

		switch msg.String() {
		case "up", "k":
			if m.cursorKey > 0 {
				m.cursorKey--
			} else if m.cursorGroup > 0 {
				m.cursorGroup--
				m.cursorKey = m.groupKeyCount() - 1
			}
		case "down", "j":
			if m.cursorKey < m.groupKeyCount()-1 {
				m.cursorKey++
			} else if m.cursorGroup < m.groupCount()-1 {
				m.cursorGroup++
				m.cursorKey = 0
			}
		case "enter":
			key := m.currentKey()
			if key != "" {
				m.editingKey = key
				m.editBuf = m.getVal(key)
			}
		case "s":
			return m, m.saveCmd()
		case "t":
			return m, m.testLLMCmd()
		case "R":
			return m, tea.Batch(m.fetchStatusCmd(), m.fetchEnvCmd())
		}
	}
	return m, nil
}

func (m SettingsModel) handleEdit(msg tea.KeyMsg) (SettingsModel, tea.Cmd) {
	switch msg.String() {
	case "enter":
		if m.env != nil && m.env.Flat != nil {
			m.env.Flat[m.editingKey] = m.editBuf
			m.successMsg = fmt.Sprintf("✎ %s updated (press s to save all)", m.editingKey)
		}
		m.editingKey = ""
	case "esc":
		m.editingKey = ""
		m.editBuf = ""
	case "backspace":
		if len(m.editBuf) > 0 {
			m.editBuf = m.editBuf[:len(m.editBuf)-1]
		}
	default:
		if len(msg.String()) == 1 {
			m.editBuf += msg.String()
		}
	}
	return m, nil
}

func (m SettingsModel) getVal(key string) string {
	if m.env != nil && m.env.Flat != nil {
		return m.env.Flat[key]
	}
	return ""
}

func (m SettingsModel) groupCount() int {
	if m.env == nil || m.env.Env == nil {
		return 0
	}
	return len(m.env.Env)
}

func (m SettingsModel) groupKeyCount() int {
	if m.env == nil || m.env.Env == nil {
		return 0
	}
	groups := m.sortedGroups()
	if m.cursorGroup >= len(groups) {
		return 0
	}
	return len(m.env.Env[groups[m.cursorGroup]])
}

func (m SettingsModel) currentKey() string {
	if m.env == nil || m.env.Env == nil {
		return ""
	}
	groups := m.sortedGroups()
	if m.cursorGroup >= len(groups) {
		return ""
	}
	group := m.env.Env[groups[m.cursorGroup]]
	keys := m.sortedKeys(group)
	if m.cursorKey >= len(keys) {
		return ""
	}
	return keys[m.cursorKey]
}

func (m SettingsModel) sortedGroups() []string {
	groups := make([]string, 0, len(m.env.Env))
	for g := range m.env.Env {
		groups = append(groups, g)
	}
	sort.Strings(groups)
	return groups
}

func (m SettingsModel) sortedKeys(data map[string]string) []string {
	keys := make([]string, 0, len(data))
	for k := range data {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return keys
}

func (m SettingsModel) View() string {
	var sb strings.Builder

	sb.WriteString(StyleTitle.Render("Settings"))
	sb.WriteString("\n\n")

	// ── Integration Status ──
	sb.WriteString(styleSection("Integration Status"))
	if m.status != nil {
		rows := []struct {
			name  string
			state string
			extra string
		}{
			{"Backend", m.status.Backend.Status, ""},
			{"Database", m.status.Database.Status, m.status.Database.URL},
			{"AI Provider", m.status.LLM.Status, m.status.LLM.Provider + " · " + m.status.LLM.Model},
			{"Stripe", m.status.Stripe.Status, ""},
			{"Notifications", m.status.Notifications.Status, ""},
			{"Redis", m.status.Redis.Status, ""},
		}
		for _, r := range rows {
			dot := "○"
			sty := StyleMuted
			switch r.state {
			case "ok", "connected", "configured":
				dot = "●"
				sty = StyleSuccess
			case "error", "missing_api_key":
				dot = "●"
				sty = StyleError
			case "not_configured":
				dot = "○"
				sty = StyleDim
			}
			line := fmt.Sprintf("  %s %s", sty.Render(dot), sty.Render(r.name))
			if r.extra != "" {
				line += StyleDim.Render(" · " + r.extra)
			}
			sb.WriteString(line + "\n")
		}
	} else {
		sb.WriteString("  Loading...\n")
	}
	sb.WriteString("\n")

	// ── Configuration Groups ──
	if m.env != nil && m.env.Env != nil {
		groups := m.sortedGroups()
		for gi, group := range groups {
			data := m.env.Env[group]
			isGroupActive := gi == m.cursorGroup

			if isGroupActive {
				sb.WriteString(StyleHighlight.Render(group))
			} else {
				sb.WriteString(StyleInfo.Render(group))
			}
			sb.WriteString("\n")

			keys := m.sortedKeys(data)
			for ki, key := range keys {
				val := data[key]
				isActive := isGroupActive && ki == m.cursorKey

				prefix := "  "
				if isActive {
					prefix = " ▸"
				}

				keyLabel := StyleMuted.Render(key + ":")
				valDisplay := val
				if val == "" {
					valDisplay = StyleDim.Render("-")
				}

				if isActive && m.editingKey == key {
					// Show editing state
					sb.WriteString(fmt.Sprintf(" %s %s %s█\n", prefix, keyLabel, StyleHighlight.Render(m.editBuf)))
					sb.WriteString(fmt.Sprintf("        %s\n", StyleDim.Render("enter confirm  ·  esc cancel")))
				} else if isActive {
					sb.WriteString(fmt.Sprintf(" %s %s %s\n", prefix, keyLabel, valDisplay))
					sb.WriteString(fmt.Sprintf("        %s\n", StyleDim.Render("enter to edit")))
				} else {
					sb.WriteString(fmt.Sprintf(" %s  %s %s\n", prefix, keyLabel, valDisplay))
				}
			}
			sb.WriteString("\n")
		}
	} else {
		sb.WriteString("  Loading config...\n\n")
	}

	// Test result
	if m.testing {
		sb.WriteString(StyleInfo.Render("  Testing LLM...") + "\n")
	}
	if m.testRes != nil {
		if m.testRes.Success {
			sb.WriteString(StyleSuccess.Render(fmt.Sprintf("  ✓ LLM OK: %s", m.testRes.Response)) + "\n")
		} else {
			sb.WriteString(StyleError.Render(fmt.Sprintf("  ✗ LLM: %s", m.testRes.Error)) + "\n")
		}
		sb.WriteString("\n")
	}

	if m.errMsg != "" {
		sb.WriteString(StyleError.Render("  ✗ "+m.errMsg) + "\n")
	}
	if m.successMsg != "" {
		sb.WriteString(StyleSuccess.Render("  "+m.successMsg) + "\n")
	}
	if m.saving {
		sb.WriteString(StyleInfo.Render("  Saving...") + "\n")
	}

	sb.WriteString("\n" + StyleDim.Render("↑↓ navigate  ·  enter edit  ·  s save  ·  t test LLM  ·  R refresh"))
	return sb.String()
}

func styleSection(title string) string {
	return StyleInfo.Render(title) + "\n" + StyleDim.Render(strings.Repeat("─", 40)) + "\n"
}
