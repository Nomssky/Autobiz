package main

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
)

func (m *model) updateApprovals(msg tea.Msg) tea.Cmd {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "up", "k":
			if m.dash.approvals.selected > 0 {
				m.dash.approvals.selected--
			}
		case "down", "j":
			if m.dash.approvals.selected < len(m.dash.approvals.approvals)-1 {
				m.dash.approvals.selected++
			}
		case "a":
			if len(m.dash.approvals.approvals) > 0 {
				approval := m.dash.approvals.approvals[m.dash.approvals.selected]
				return m.decideApproval(approval.ID, true)
			}
		case "r":
			if len(m.dash.approvals.approvals) > 0 {
				approval := m.dash.approvals.approvals[m.dash.approvals.selected]
				return m.decideApproval(approval.ID, false)
			}
		case "enter":
			if len(m.dash.approvals.approvals) > 0 {
				m.dash.approvals.showDetails = !m.dash.approvals.showDetails
			}
		}
	}
	return nil
}

func (m *model) decideApproval(id string, approve bool) tea.Cmd {
	return func() tea.Msg {
		err := m.api.decideApproval(id, m.user.UserID, approve, "")
		if err != nil {
			return errMsg{err}
		}
		return successMsg{"Decision recorded"}
	}
}

func (m *model) approvalsView() string {
	var b strings.Builder

	b.WriteString(titleStyle.Render("Approvals"))
	b.WriteString("\n\n")

	if m.dash.approvals.loading {
		b.WriteString(infoStyle.Render("Loading..."))
		return b.String()
	}

	if len(m.dash.approvals.approvals) == 0 {
		b.WriteString(dimStyle.Render("No pending approvals."))
		b.WriteString("\n\n")
		b.WriteString(helpStyle.Render("q: quit"))
		return b.String()
	}

	for i, a := range m.dash.approvals.approvals {
		prefix := "  "
		if i == m.dash.approvals.selected {
			prefix = "▸ "
		}

		urgencyStyle := infoStyle
		if a.Urgency == "high" || a.Urgency == "critical" {
			urgencyStyle = warnStyle
		}

		line := fmt.Sprintf("%s%s  %s", prefix, a.Title, urgencyStyle.Render(a.Urgency))
		if i == m.dash.approvals.selected {
			b.WriteString(selectedStyle.Render(line))
		} else {
			b.WriteString(line)
		}
		b.WriteString("\n")

		// Show detail if selected + expanded
		if i == m.dash.approvals.selected && m.dash.approvals.showDetails {
			b.WriteString(fmt.Sprintf("    %s\n", dimStyle.Render(a.Description)))
			b.WriteString("\n")
		}
	}

	b.WriteString("\n")
	b.WriteString(helpStyle.Render("↑↓: navigate • a: approve • r: reject • enter: toggle detail • q: quit"))
	return b.String()
}
