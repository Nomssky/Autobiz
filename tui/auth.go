package main

import (
	"strings"

	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

type authModel struct {
	state       appState
	emailInput  textinput.Model
	userInput   textinput.Model
	passInput   textinput.Model
	focusIndex  int
	loading     bool
	err         string
	api         *apiClient
}

func newAuthModel(api *apiClient) authModel {
	email := textinput.New()
	email.Placeholder = "Email"
	email.CharLimit = 100
	email.Width = 40

	user := textinput.New()
	user.Placeholder = "Username"
	user.CharLimit = 100
	user.Width = 40

	pass := textinput.New()
	pass.Placeholder = "Password"
	pass.EchoMode = textinput.EchoPassword
	pass.CharLimit = 100
	pass.Width = 40

	return authModel{
		state:      stateLogin,
		emailInput: email,
		userInput:  user,
		passInput:  pass,
		focusIndex: 0,
		api:        api,
	}
}

func (m authModel) Init() tea.Cmd {
	return textinput.Blink
}

func (m authModel) Update(msg tea.Msg) (authModel, tea.Cmd) {
	var cmds []tea.Cmd

	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "esc":
			return m, tea.Quit
		case "tab", "shift+tab", "up", "down":
			if msg.String() == "up" || msg.String() == "shift+tab" {
				m.focusIndex--
				if m.focusIndex < 0 {
					m.focusIndex = m.fieldCount() - 1
				}
			} else {
				m.focusIndex++
				if m.focusIndex >= m.fieldCount() {
					m.focusIndex = 0
				}
			}
			m.updateFocus()
		case "enter":
			if !m.loading && m.focusIndex == m.fieldCount()-1 {
				m.loading = true
				m.err = ""
				if m.state == stateLogin {
					return m, m.login()
				}
				return m, m.register()
			}
		}
	case errMsg:
		m.loading = false
		m.err = msg.Error()
	case loggedInMsg:
		m.loading = false
		return m, func() tea.Msg { return msg }
	}

	cmd := m.updateInputs(msg)
	cmds = append(cmds, cmd)
	return m, tea.Batch(cmds...)
}

func (m *authModel) fieldCount() int {
	if m.state == stateRegister {
		return 4 // email, username, password, submit
	}
	return 3 // email, password, submit
}

func (m *authModel) updateFocus() {
	focused := 0
	if m.state == stateRegister {
		if m.focusIndex == 0 {
			m.emailInput.Focus()
			m.userInput.Blur()
			m.passInput.Blur()
		} else if m.focusIndex == 1 {
			m.emailInput.Blur()
			m.userInput.Focus()
			m.passInput.Blur()
		} else if m.focusIndex == 2 {
			m.emailInput.Blur()
			m.userInput.Blur()
			m.passInput.Focus()
		}
		focused = m.focusIndex
	} else {
		if m.focusIndex == 0 {
			m.emailInput.Focus()
			m.passInput.Blur()
		} else if m.focusIndex == 1 {
			m.emailInput.Blur()
			m.passInput.Focus()
		}
		focused = m.focusIndex
	}
	if m.state == stateRegister && focused > 2 {
		m.emailInput.Blur()
		m.userInput.Blur()
		m.passInput.Blur()
	} else if m.state == stateLogin && focused > 1 {
		m.emailInput.Blur()
		m.passInput.Blur()
	}
}

func (m authModel) updateInputs(msg tea.Msg) tea.Cmd {
	var cmds []tea.Cmd
	var cmd tea.Cmd

	m.emailInput, cmd = m.emailInput.Update(msg)
	cmds = append(cmds, cmd)
	if m.state == stateRegister {
		m.userInput, cmd = m.userInput.Update(msg)
		cmds = append(cmds, cmd)
	}
	m.passInput, cmd = m.passInput.Update(msg)
	cmds = append(cmds, cmd)

	return tea.Batch(cmds...)
}

func (m authModel) login() tea.Cmd {
	return func() tea.Msg {
		u, err := m.api.login(m.emailInput.Value(), m.passInput.Value())
		if err != nil {
			return errMsg{err}
		}
		m.api.setToken(u.Token)
		return loggedInMsg{u}
	}
}

func (m authModel) register() tea.Cmd {
	return func() tea.Msg {
		u, err := m.api.register(m.emailInput.Value(), m.userInput.Value(), m.passInput.Value())
		if err != nil {
			return errMsg{err}
		}
		m.api.setToken(u.Token)
		return loggedInMsg{u}
	}
}

func (m authModel) View() string {
	var b strings.Builder

	b.WriteString(titleStyle.Render("AutoBiz Engine"))
	b.WriteString("\n\n")

	if m.state == stateLogin {
		b.WriteString(subtitleStyle.Render("Login to your account"))
	} else {
		b.WriteString(subtitleStyle.Render("Create a new account"))
	}
	b.WriteString("\n\n")

	b.WriteString(lipgloss.NewStyle().PaddingLeft(2).Render("Email:"))
	b.WriteString("\n")
	b.WriteString(lipgloss.NewStyle().PaddingLeft(2).Render(m.emailInput.View()))
	b.WriteString("\n\n")

	if m.state == stateRegister {
		b.WriteString(lipgloss.NewStyle().PaddingLeft(2).Render("Username:"))
		b.WriteString("\n")
		b.WriteString(lipgloss.NewStyle().PaddingLeft(2).Render(m.userInput.View()))
		b.WriteString("\n\n")
	}

	b.WriteString(lipgloss.NewStyle().PaddingLeft(2).Render("Password:"))
	b.WriteString("\n")
	b.WriteString(lipgloss.NewStyle().PaddingLeft(2).Render(m.passInput.View()))
	b.WriteString("\n\n")

	if m.loading {
		b.WriteString(lipgloss.NewStyle().PaddingLeft(2).Foreground(lipgloss.Color("#7B59E0")).Render("Authenticating..."))
	} else {
		btnIndex := 2
		if m.state == stateRegister {
			btnIndex = 3
		}
		if m.focusIndex == btnIndex {
			b.WriteString(lipgloss.NewStyle().PaddingLeft(2).Render(buttonStyle.Render("  Submit  ")))
		} else {
			b.WriteString(lipgloss.NewStyle().PaddingLeft(2).Render(
				lipgloss.NewStyle().Foreground(lipgloss.Color("#626262")).Render("[ Submit ]"),
			))
		}
	}

	if m.err != "" {
		b.WriteString("\n\n")
		b.WriteString(errorStyle.Render("Error: " + m.err))
	}

	b.WriteString("\n\n")
	b.WriteString(helpStyle.Render("tab: navigate • enter: submit • esc: quit"))

	if m.state == stateLogin {
		b.WriteString("\n")
		b.WriteString(helpStyle.Render("Don't have an account? Press 'r' to register"))
	} else {
		b.WriteString("\n")
		b.WriteString(helpStyle.Render("Already have an account? Press 'l' to login"))
	}

	return appStyle.Render(b.String())
}
