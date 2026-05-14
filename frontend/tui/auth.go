package main

import (
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

type authState int

const (
	authInputEmail authState = iota
	authInputPassword
	authInputName
	authDone
)

type authModel struct {
	state      authState
	api        *apiClient
	email      string
	password   string
	name       string
	err        string
	focusIndex int
}

func newAuthModel(api *apiClient) authModel {
	return authModel{api: api, state: authInputEmail}
}

func (m authModel) Init() tea.Cmd { return nil }

func (m authModel) Update(msg tea.Msg) (authModel, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "enter":
			return m.advance()
		case "backspace":
			return m.deleteChar(), nil
		default:
			if len(msg.String()) == 1 {
				return m.addChar(msg.String()), nil
			}
		}
	}
	return m, nil
}

func (m authModel) addChar(ch string) authModel {
	switch m.state {
	case authInputEmail:
		m.email += ch
	case authInputPassword:
		m.password += ch
	case authInputName:
		m.name += ch
	}
	return m
}

func (m authModel) deleteChar() authModel {
	switch m.state {
	case authInputEmail:
		if len(m.email) > 0 {
			m.email = m.email[:len(m.email)-1]
		}
	case authInputPassword:
		if len(m.password) > 0 {
			m.password = m.password[:len(m.password)-1]
		}
	case authInputName:
		if len(m.name) > 0 {
			m.name = m.name[:len(m.name)-1]
		}
	}
	return m
}

func (m authModel) advance() (authModel, tea.Cmd) {
	switch m.state {
	case authInputEmail:
		if m.email == "" {
			m.err = "Email is required"
			return m, nil
		}
		m.state = authInputPassword
		m.err = ""
	case authInputPassword:
		if m.password == "" {
			m.err = "Password is required"
			return m, nil
		}
		m.state = authInputName
		m.err = ""
	case authInputName:
		m.state = authDone
		m.err = ""
		return m, m.loginOrRegister()
	}
	return m, nil
}

func (m authModel) loginOrRegister() tea.Cmd {
	return func() tea.Msg {
		if m.name == "" {
			u, err := m.api.login(m.email, m.password)
			if err != nil {
				return errMsg{err}
			}
			return loggedInMsg{user: u}
		}
		u, err := m.api.register(m.email, m.name, m.password)
		if err != nil {
			return errMsg{err}
		}
		return loggedInMsg{user: u}
	}
}

func (m authModel) View() string {
	var b strings.Builder

	b.WriteString(titleStyle.Render("AutoBiz Engine"))
	b.WriteString("\n\n")

	switch m.state {
	case authInputEmail:
		b.WriteString(inputStyle.Render("Email:"))
		b.WriteString("\n")
		b.WriteString(valueStyle.Render(m.email + cursor()))
	case authInputPassword:
		b.WriteString(inputStyle.Render("Password:"))
		b.WriteString("\n")
		b.WriteString(valueStyle.Render(strings.Repeat("•", len(m.password)) + cursor()))
	case authInputName:
		b.WriteString(inputStyle.Render("Name (leave empty to login):"))
		b.WriteString("\n")
		b.WriteString(valueStyle.Render(m.name + cursor()))
	}

	if m.err != "" {
		b.WriteString("\n\n")
		b.WriteString(errorStyle.Render("Error: " + m.err))
	}

	b.WriteString("\n\n")
	b.WriteString(helpStyle.Render("Enter: next • Backspace: delete • Ctrl+C: quit"))
	return appStyle.Render(b.String())
}

func cursor() string {
	return lipgloss.NewStyle().Foreground(lipgloss.Color("36")).Render("█")
}
