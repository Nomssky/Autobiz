package ui

import (
	"autobiz/internal/api"
	"fmt"
	"strings"

	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
)

type bizPage int

const (
	bizPageList bizPage = iota
	bizPageCreate
	bizPageDetail
)

type BizModel struct {
	client     *api.Client
	page       bizPage
	items      []api.Business
	cursor     int
	detail     *api.Business
	input      textinput.Model
	errMsg     string
	statusMsg  string
	loading    bool
}

// messages
type BizListMsg struct{ Items []api.Business }
type BizCreatedMsg struct{ B api.Business }
type BizErrMsg struct{ Err string }
type BizStatusMsg struct{ Msg string }

func (m BizModel) Items() []api.Business { return m.items }

func NewBizModel(client *api.Client) BizModel {
	t := textinput.New()
	t.Placeholder = "Describe your business idea…"
	t.Width = 50
	return BizModel{client: client, input: t}
}

func (m BizModel) fetchCmd() tea.Cmd {
	return func() tea.Msg {
		items, err := m.client.ListBusinesses()
		if err != nil {
			return BizErrMsg{Err: err.Error()}
		}
		return BizListMsg{Items: items}
	}
}

func (m BizModel) createCmd(idea string) tea.Cmd {
	return func() tea.Msg {
		b, err := m.client.CreateBusiness(idea)
		if err != nil {
			return BizErrMsg{Err: err.Error()}
		}
		return BizCreatedMsg{B: *b}
	}
}

func (m BizModel) Init() tea.Cmd { return m.fetchCmd() }

func (m BizModel) Update(msg tea.Msg) (BizModel, tea.Cmd) {
	var cmd tea.Cmd

	switch msg := msg.(type) {
	case BizListMsg:
		m.loading = false
		m.items = msg.Items
		if m.cursor >= len(m.items) && len(m.items) > 0 {
			m.cursor = len(m.items) - 1
		}

	case BizCreatedMsg:
		m.loading = false
		m.page = bizPageList
		m.statusMsg = fmt.Sprintf("Business '%s' created!", msg.B.Name)
		m.input.SetValue("")
		return m, m.fetchCmd()

	case BizErrMsg:
		m.loading = false
		m.errMsg = msg.Err

	case BizStatusMsg:
		m.statusMsg = msg.Msg

	case tea.KeyMsg:
		m.errMsg = ""
		m.statusMsg = ""

		switch m.page {
		case bizPageList:
			switch msg.String() {
			case "up", "k":
				if m.cursor > 0 {
					m.cursor--
				}
			case "down", "j":
				if m.cursor < len(m.items)-1 {
					m.cursor++
				}
			case "enter":
				if len(m.items) > 0 {
					d := m.items[m.cursor]
					m.detail = &d
					m.page = bizPageDetail
				}
			case "n":
				m.page = bizPageCreate
				m.input.Focus()
			case "r":
				m.loading = true
				return m, m.fetchCmd()
			}

		case bizPageCreate:
			switch msg.Type {
			case tea.KeyEnter:
				idea := strings.TrimSpace(m.input.Value())
				if idea != "" {
					m.loading = true
					return m, m.createCmd(idea)
				}
			case tea.KeyEsc:
				m.page = bizPageList
				m.input.Blur()
				m.input.SetValue("")
			default:
				m.input, cmd = m.input.Update(msg)
			}

		case bizPageDetail:
			switch msg.String() {
			case "esc", "q":
				m.page = bizPageList
				m.detail = nil
			}
		}
	}

	return m, cmd
}

func (m BizModel) View() string {
	var sb strings.Builder

	switch m.page {
	case bizPageList:
		sb.WriteString(StyleTitle.Render("Businesses") + "\n\n")

		if m.loading {
			sb.WriteString(StyleMuted.Render("  loading…") + "\n")
		} else if len(m.items) == 0 {
			sb.WriteString(StyleMuted.Render("  No businesses yet.") + "\n")
			sb.WriteString(StyleDim.Render("  Press n to create your first one.") + "\n")
		} else {
			for i, b := range m.items {
				cursor := "  "
				nameStyle := StyleNormal
				if i == m.cursor {
					cursor = StyleSelected.Render("▸ ")
					nameStyle = StyleSelected
				}
				phase := StatusStyle(b.CurrentPhase).Render(b.CurrentPhase)
				sb.WriteString(fmt.Sprintf("%s%s  %s\n",
					cursor, nameStyle.Render(b.Name), phase))
			}
		}

		if m.errMsg != "" {
			sb.WriteString("\n" + StyleError.Render("✗ "+m.errMsg) + "\n")
		}
		if m.statusMsg != "" {
			sb.WriteString("\n" + StyleSuccess.Render("✓ "+m.statusMsg) + "\n")
		}

		sb.WriteString("\n" + StyleDim.Render("↑↓/jk navigate  ·  enter detail  ·  n new  ·  r refresh"))

	case bizPageCreate:
		sb.WriteString(StyleTitle.Render("New Business") + "\n\n")
		sb.WriteString(StyleMuted.Render("Describe your idea and AutoBiz will handle the rest.") + "\n\n")
		sb.WriteString(StyleInputLabel.Render("Idea") + "\n")
		sb.WriteString(m.input.View() + "\n\n")

		if m.loading {
			sb.WriteString(StyleInfo.Render("  Creating your business…") + "\n")
		}
		if m.errMsg != "" {
			sb.WriteString(StyleError.Render("✗ "+m.errMsg) + "\n")
		}

		sb.WriteString("\n" + StyleDim.Render("enter create  ·  esc back"))

	case bizPageDetail:
		d := m.detail
		sb.WriteString(StyleTitle.Render(d.Name) + "\n\n")
		row := func(label, value string) string {
			return StyleInfo.Render(label+":") + "  " + StyleNormal.Render(value) + "\n"
		}
		shortID := d.ID
		if len(shortID) > 12 {
			shortID = shortID[:12] + "…"
		}
		createdAt := d.CreatedAt
		if len(createdAt) > 10 {
			createdAt = createdAt[:10]
		}
		sb.WriteString(row("ID", shortID))
		sb.WriteString(row("Status", StatusStyle(d.Status).Render(d.Status)))
		sb.WriteString(row("Phase", d.CurrentPhase))
		sb.WriteString(row("Created", createdAt))
		if d.Description != "" {
			sb.WriteString("\n" + StyleMuted.Render(d.Description) + "\n")
		}
		sb.WriteString("\n" + StyleDim.Render("esc back"))
	}

	return sb.String()
}