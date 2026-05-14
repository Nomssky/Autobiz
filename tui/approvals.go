package main

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

func (m *model) updateApprovals(msg tea.Msg) tea.Cmd {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "up", "k":
			if len(m.dash.approvals.approvals) > 0 {
				m.dash.approvals.selected--
				if m.dash.approvals.selected < 0 {
					m.dash.approvals.selected = len(m.dash.approvals.approvals) - 1
				}
			}
		case "down", "j":
			if len(m.dash.approvals.approvals) > 0 {
				m.dash.approvals.selected++
				if m.dash.approvals.selected >= len(m.dash.approvals.approvals) {
					m.dash.approvals.selected = 0
				}
			}
		case "enter":
			if len(m.dash.approvals.approvals) > 0 {
				sel := m.dash.approvals.approvals[m.dash.approvals.selected]
				m.dash.approvals.detail = sel
				m.dash.approvals.showDetails = !m.dash.approvals.showDetails
			}
		case "a":
			if len(m.dash.approvals.approvals) > 0 {
				sel := m.dash.approvals.approvals[m.dash.approvals.selected]
				m.dash.approvals.loading = true
				return m.decideApproval(sel.ID, true, "Approved via TUI")
			}
		case "r":
			if msg.String() == "r" && !m.dash.approvals.showDetails {
				if len(m.dash.approvals.approvals) > 0 {
					sel := m.dash.approvals.approvals[m.dash.approvals.selected]
					m.dash.approvals.loading = true
					return m.decideApproval(sel.ID, false, "Rejected via TUI")
				}
			}
		case "esc":
			m.dash.approvals.showDetails = false
		}
	}
	return nil
}

func (m *model) decideApproval(id int, approved bool, reason string) tea.Cmd {
	return func() tea.Msg {
		err := m.api.decideApproval(id, approved, reason)
		if err != nil {
			m.dash.approvals.loading = false
			return errMsg{err}
		}
		m.dash.approvals.loading = false
		return m.loadApprovals()
	}
}

func (m model) approvalsView() string {
	var b strings.Builder

	b.WriteString(titleStyle.Render("Pending Approvals"))
	b.WriteString("\n\n")

	if m.dash.approvals.showDetails {
		return m.approvalDetailView()
	}

	if m.dash.approvals.loading {
		b.WriteString(spinnerStyle.Render("Loading approvals..."))
		return b.String()
	}

	if len(m.dash.approvals.approvals) == 0 {
		b.WriteString(subtitleStyle.Render("No pending approvals!"))
		b.WriteString("\n\n")
		b.WriteString(helpStyle.Render("q: quit"))
		return b.String()
	}

	for i, a := range m.dash.approvals.approvals {
		line := fmt.Sprintf("%s  %s  — %s",
			a.BusinessName,
			a.Title,
			a.AgentName,
		)

		if i == m.dash.approvals.selected {
			b.WriteString(selectedItemStyle.Render("▸ " + line))
		} else {
			b.WriteString(itemStyle.Render("  " + line))
		}
		b.WriteString("\n")
	}

	b.WriteString("\n")
	b.WriteString(helpStyle.Render("↑/↓: navigate • a: approve • r: reject • enter: details • q: quit"))

	return b.String()
}

func (m model) approvalDetailView() string {
	var b strings.Builder
	a := m.dash.approvals.detail

	b.WriteString(titleStyle.Render("Approval Details"))
	b.WriteString("\n\n")

	b.WriteString(detailStyle.Render(
		lipgloss.JoinVertical(lipgloss.Left,
			"Business: "+a.BusinessName,
			"Title: "+a.Title,
			"Agent: "+a.AgentName,
			"",
			"Summary:",
			a.Summary,
			"",
			"Details:",
			a.Details,
		),
	))
	b.WriteString("\n\n")

	b.WriteString(lipgloss.JoinHorizontal(lipgloss.Center,
		approveBtnStyle.Render("(a) Approve"),
		rejectBtnStyle.Render("(r) Reject"),
	))
	b.WriteString("\n\n")

	b.WriteString(helpStyle.Render("a: approve • r: reject • esc: back • q: quit"))

	return b.String()
}
