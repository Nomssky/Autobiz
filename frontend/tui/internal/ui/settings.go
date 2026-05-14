package ui

import (
	"autobiz/internal/api"
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
)

type editField int

const (
	fieldProvider editField = iota
	fieldModel
	fieldAPIKey
	fieldBaseURL
	fieldEmbedProvider
	fieldEmbedModel
	fieldOllamaURL
	fieldNone
)

type SettingsModel struct {
	client      *api.Client
	status      *api.IntegrationStatus
	env         *api.EnvConfig
	testRes     *api.TestLLMResult
	testing     bool
	saving      bool
	editing     editField
	editBuf     string
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
		if m.env == nil {
			return SavedMsg{Err: "no config loaded"}
		}
		err := m.client.SaveEnv(m.env.Env)
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
			m.successMsg = "✓ Settings saved"
		}
	case SettingsErrMsg:
		m.errMsg = msg.Err

	case tea.KeyMsg:
		m.errMsg = ""
		m.successMsg = ""

		if m.editing != fieldNone {
			return m.handleEdit(msg)
		}

		switch msg.String() {
		case "1":
			m.editing = fieldProvider
			m.editBuf = m.getVal("LLM_PROVIDER")
		case "2":
			m.editing = fieldModel
			m.editBuf = m.getVal("LLM_MODEL")
		case "3":
			m.editing = fieldAPIKey
			m.editBuf = m.getVal("LLM_API_KEY")
		case "4":
			m.editing = fieldBaseURL
			m.editBuf = m.getVal("LLM_BASE_URL")
		case "5":
			m.editing = fieldEmbedProvider
			m.editBuf = m.getVal("EMBEDDING_PROVIDER")
		case "6":
			m.editing = fieldEmbedModel
			m.editBuf = m.getVal("EMBEDDING_MODEL")
		case "7":
			m.editing = fieldOllamaURL
			m.editBuf = m.getVal("OLLAMA_BASE_URL")
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
		m.saveField()
		m.editing = fieldNone
	case "esc":
		m.editing = fieldNone
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

func (m SettingsModel) saveField() {
	if m.env == nil || m.env.Env == nil {
		return
	}
	keys := map[editField]string{
		fieldProvider:     "LLM_PROVIDER",
		fieldModel:         "LLM_MODEL",
		fieldAPIKey:       "LLM_API_KEY",
		fieldBaseURL:      "LLM_BASE_URL",
		fieldEmbedProvider: "EMBEDDING_PROVIDER",
		fieldEmbedModel:    "EMBEDDING_MODEL",
		fieldOllamaURL:    "OLLAMA_BASE_URL",
	}
	key := keys[m.editing]
	m.env.Env[key] = m.editBuf
	m.successMsg = fmt.Sprintf("✎ %s updated (press s to save)", key)
}

func (m SettingsModel) getVal(key string) string {
	if m.env != nil && m.env.Env != nil {
		return m.env.Env[key]
	}
	return ""
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
			{"LLM", m.status.LLM.Status, m.status.LLM.Provider + " · " + m.status.LLM.Model},
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
			}
			line := fmt.Sprintf("  %s %s", sty.Render(dot), sty.Render(r.name))
			if r.extra != "" {
				line += StyleDim.Render(" · " + r.extra)
			}
			sb.WriteString(line + "\n")
		}
	} else {
		sb.WriteString("  ...\n")
	}
	sb.WriteString("\n")

	// ── Editable Fields ──
	sb.WriteString(styleSection("AI Provider Configuration"))
	sb.WriteString("\n")

	editableFields := []struct {
		key    string
		label  string
		hotkey string
		field  editField
	}{
		{"LLM_PROVIDER", "Provider", "1", fieldProvider},
		{"LLM_MODEL", "Model", "2", fieldModel},
		{"LLM_API_KEY", "API Key", "3", fieldAPIKey},
		{"LLM_BASE_URL", "Base URL", "4", fieldBaseURL},
		{"EMBEDDING_PROVIDER", "Embed Provider", "5", fieldEmbedProvider},
		{"EMBEDDING_MODEL", "Embed Model", "6", fieldEmbedModel},
		{"OLLAMA_BASE_URL", "Ollama URL", "7", fieldOllamaURL},
	}

	for _, f := range editableFields {
		val := m.getVal(f.key)
		if val == "" {
			val = "-"
		}

		isEditing := m.editing == f.field
		prefix := "  "
		if isEditing {
			prefix = " ✎"
		}

		label := fmt.Sprintf("%s%s:", StyleInfo.Render(prefix), StyleMuted.Render(" "+f.label))
		sb.WriteString(fmt.Sprintf("%s  %s\n", label, val))

		if isEditing {
			sb.WriteString(fmt.Sprintf("     %s█\n", StyleHighlight.Render(m.editBuf)))
			sb.WriteString(StyleDim.Render("     enter confirm  ·  esc cancel") + "\n")
		} else {
			sb.WriteString(fmt.Sprintf("     %s\n", StyleDim.Render(fmt.Sprintf("[%s] edit", f.hotkey))))
		}
	}

	sb.WriteString("\n")

	// ── Test Result ──
	if m.testing {
		sb.WriteString(StyleInfo.Render("  Testing LLM connection...") + "\n\n")
	}
	if m.testRes != nil {
		if m.testRes.Success {
			sb.WriteString(StyleSuccess.Render(fmt.Sprintf("  ✓ LLM OK: %s", m.testRes.Response)) + "\n\n")
		} else {
			sb.WriteString(StyleError.Render(fmt.Sprintf("  ✗ LLM failed: %s", m.testRes.Error)) + "\n\n")
		}
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

	sb.WriteString("\n" + StyleDim.Render("1-7 edit fields  ·  s save  ·  t test  ·  R refresh"))
	return sb.String()
}

func styleSection(title string) string {
	return StyleInfo.Render(title) + "\n" + StyleDim.Render(strings.Repeat("─", 40)) + "\n"
}
