package ui

import (
	"autobiz/internal/api"
	"strings"

	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

type authStep int

const (
	stepEmail authStep = iota
	stepPassword
	stepName
)

type AuthModel struct {
	client   *api.Client
	step     authStep
	email    textinput.Model
	password textinput.Model
	name     textinput.Model
	err      string
	loading  bool
	isLogin  bool // true = trying login, flip to register if name filled
}

type LoginSuccessMsg struct{ Client *api.Client }
type LoginErrMsg struct{ Err string }

func NewAuthModel(client *api.Client) AuthModel {
	mkInput := func(placeholder string, echo rune) textinput.Model {
		t := textinput.New()
		t.Placeholder = placeholder
		t.EchoCharacter = echo
		t.Width = 36
		return t
	}

	email := mkInput("you@example.com", 0)
	email.Focus()

	password := mkInput("••••••••", '•')
	name := mkInput("leave blank to login", 0)

	return AuthModel{
		client:   client,
		step:     stepEmail,
		email:    email,
		password: password,
		name:     name,
		isLogin:  true,
	}
}

func (m AuthModel) Init() tea.Cmd { return textinput.Blink }

func (m AuthModel) Update(msg tea.Msg) (AuthModel, tea.Cmd) {
	var cmd tea.Cmd

	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.Type {
		case tea.KeyEnter:
			switch m.step {
			case stepEmail:
				m.step = stepPassword
				m.email.Blur()
				m.password.Focus()
			case stepPassword:
				m.step = stepName
				m.password.Blur()
				m.name.Focus()
			case stepName:
				return m, m.submit()
			}
			return m, nil

		case tea.KeyEsc:
			if m.step > stepEmail {
				m.step--
				switch m.step {
				case stepEmail:
					m.password.Blur()
					m.email.Focus()
				case stepPassword:
					m.name.Blur()
					m.password.Focus()
				}
			}
			return m, nil
		}

	case LoginSuccessMsg:
		m.loading = false
		return m, nil

	case LoginErrMsg:
		m.loading = false
		m.err = msg.Err
		return m, nil
	}

	// Route input to active field
	switch m.step {
	case stepEmail:
		m.email, cmd = m.email.Update(msg)
	case stepPassword:
		m.password, cmd = m.password.Update(msg)
	case stepName:
		m.name, cmd = m.name.Update(msg)
	}
	return m, cmd
}

func (m AuthModel) submit() tea.Cmd {
	return func() tea.Msg {
		nameVal := strings.TrimSpace(m.name.Value())
		email := strings.TrimSpace(m.email.Value())
		pass := m.password.Value()

		var authResp *api.AuthResponse
		var err error

		if nameVal == "" {
			authResp, err = m.client.Login(email, pass)
		} else {
			authResp, err = m.client.Register(email, pass, nameVal)
		}

		if err != nil {
			return LoginErrMsg{Err: err.Error()}
		}

		m.client.Token = authResp.AccessToken
		m.client.UserEmail = authResp.Email
		m.client.UserName = authResp.Name
		m.client.UserID = authResp.UserID
		return LoginSuccessMsg{Client: m.client}
	}
}

func (m AuthModel) View() string {
	var sb strings.Builder

	sb.WriteString(StyleTitle.Render("AutoBiz Engine") + "\n")
	sb.WriteString(StyleMuted.Render("build AI-powered businesses") + "\n\n")

	field := func(label string, input textinput.Model, active bool) string {
		lStyle := StyleInputLabel
		if !active {
			lStyle = StyleMuted
		}
		return lStyle.Render(label) + "\n" + input.View() + "\n\n"
	}

	sb.WriteString(field("Email", m.email, m.step == stepEmail))
	sb.WriteString(field("Password", m.password, m.step == stepPassword))
	sb.WriteString(field("Name  "+StyleMuted.Render("(leave blank to login)"), m.name, m.step == stepName))

	if m.err != "" {
		sb.WriteString(StyleError.Render("✗ "+m.err) + "\n\n")
	}

	// progress dots
	dots := []string{"○", "○", "○"}
	dots[m.step] = StyleHighlight.Render("●")
	sb.WriteString(strings.Join(dots, " ") + "\n\n")

	// help
	helps := []string{
		StyleHelp.Render("enter") + " next",
		StyleHelp.Render("esc") + " back",
		StyleHelp.Render("ctrl+c") + " quit",
	}
	sb.WriteString(lipgloss.JoinHorizontal(lipgloss.Top,
		intersperse(helps, StyleDim.Render("  ·  "))...) + "\n")

	return StyleApp.Render(sb.String())
}

func intersperse(ss []string, sep string) []string {
	out := make([]string, 0, len(ss)*2-1)
	for i, s := range ss {
		if i > 0 {
			out = append(out, sep)
		}
		out = append(out, s)
	}
	return out
}