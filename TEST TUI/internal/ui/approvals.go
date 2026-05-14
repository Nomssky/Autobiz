package ui

import (
	"autobiz/internal/api"
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
)

type ApprovalModel struct {
	client *api.Client
	items  []api.Approval
	cursor int
	errMsg string
}

func NewApprovalModel(client *api.Client) ApprovalModel {
	return ApprovalModel{client: client}
}

func (m ApprovalModel) Items() []api.Approval    { return m.items }
func (m ApprovalModel) PendingCount() int {
	count := 0
	for _, a := range m.items {
		if a.Status == "" || a.Status == "pending" {
			count++
		}
	}
	return count
}

type ApprovalListMsg struct{ Items []api.Approval }
type ApprovalErrMsg struct{ Err string }

func (m ApprovalModel) fetchCmd() tea.Cmd {
	return func() tea.Msg {
		items, err := m.client.ListApprovals()
		if err != nil {
			return ApprovalErrMsg{Err: err.Error()}
		}
		return ApprovalListMsg{Items: items}
	}
}

func (m ApprovalModel) Init() tea.Cmd { return m.fetchCmd() }

func (m ApprovalModel) Update(msg tea.Msg) (ApprovalModel, tea.Cmd) {
	switch msg := msg.(type) {
	case ApprovalListMsg:
		m.items = msg.Items
		if m.cursor >= len(m.items) && len(m.items) > 0 {
			m.cursor = len(m.items) - 1
		}

	case ApprovalErrMsg:
		m.errMsg = msg.Err

	case tea.KeyMsg:
		m.errMsg = ""
		switch msg.String() {
		case "up", "k":
			if m.cursor > 0 {
				m.cursor--
			}
		case "down", "j":
			if m.cursor < len(m.items)-1 {
				m.cursor++
			}
		case "a":
			if len(m.items) > 0 {
				id := m.items[m.cursor].ID
				return m, m.decideCmd(id, "approve")
			}
		case "r":
			if len(m.items) > 0 {
				id := m.items[m.cursor].ID
				return m, m.decideCmd(id, "reject")
			}
		case "R":
			return m, m.fetchCmd()
		}
	}
	return m, nil
}

func (m ApprovalModel) decideCmd(id, decision string) tea.Cmd {
	return func() tea.Msg {
		if err := m.client.DecideApproval(id, decision); err != nil {
			return ApprovalErrMsg{Err: err.Error()}
		}
		return m.fetchCmd()()
	}
}

func (m ApprovalModel) View() string {
	var sb strings.Builder

	sb.WriteString(StyleTitle.Render("Approvals") + "\n\n")

	if len(m.items) == 0 {
		sb.WriteString(StyleMuted.Render("  No approvals yet.") + "\n")
		sb.WriteString("\n" + StyleDim.Render("R refresh"))
		return sb.String()
	}

	for i, a := range m.items {
		cursor := "  "
		nameStyle := StyleNormal
		if i == m.cursor {
			cursor = StyleSelected.Render("▸ ")
			nameStyle = StyleSelected
		}
		urgency := UrgencyStyle(a.Urgency).Render(strings.ToUpper(a.Urgency))
		sb.WriteString(fmt.Sprintf("%s%s  %s\n", cursor, nameStyle.Render(a.Title), urgency))
	}

	if m.errMsg != "" {
		sb.WriteString("\n" + StyleError.Render("✗ "+m.errMsg) + "\n")
	}

	sb.WriteString("\n" + StyleDim.Render("↑↓/jk navigate  ·  a approve  ·  r reject  ·  R refresh"))
	return sb.String()
}
