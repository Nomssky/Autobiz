package main

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

func (m *model) updateBusinesses(msg tea.Msg) tea.Cmd {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "esc":
			if m.dash.businesses.page == pageDetail || m.dash.businesses.page == pageCreate {
				m.dash.businesses.page = pageList
				return nil
			}
		case "up", "k":
			if m.dash.businesses.page == pageList && len(m.dash.businesses.businesses) > 0 {
				m.dash.businesses.selected--
				if m.dash.businesses.selected < 0 {
					m.dash.businesses.selected = len(m.dash.businesses.businesses) - 1
				}
			}
		case "down", "j":
			if m.dash.businesses.page == pageList && len(m.dash.businesses.businesses) > 0 {
				m.dash.businesses.selected++
				if m.dash.businesses.selected >= len(m.dash.businesses.businesses) {
					m.dash.businesses.selected = 0
				}
			}
		case "enter":
			if m.dash.businesses.page == pageList && len(m.dash.businesses.businesses) > 0 {
				return m.loadBusinessDetail(m.dash.businesses.businesses[m.dash.businesses.selected].ID)
			}
		case "n":
			if m.dash.businesses.page == pageList {
				m.dash.businesses.page = pageCreate
				m.dash.businesses.ideaInput = ""
			}
		case "r":
			if m.dash.businesses.page == pageList {
				m.dash.businesses.loading = true
				return m.loadBusinesses()
			}
		case "backspace":
			if m.dash.businesses.page == pageCreate && len(m.dash.businesses.ideaInput) > 0 {
				m.dash.businesses.ideaInput = m.dash.businesses.ideaInput[:len(m.dash.businesses.ideaInput)-1]
			}
		}

		if m.dash.businesses.page == pageCreate {
			switch msg.String() {
			case "enter":
				if !m.dash.businesses.creating && len(m.dash.businesses.ideaInput) > 0 {
					m.dash.businesses.creating = true
					return m.createBusiness(m.dash.businesses.ideaInput)
				}
			default:
				if len(msg.String()) == 1 && msg.String() != "n" && msg.String() != "r" && msg.String() != "esc" {
					m.dash.businesses.ideaInput += msg.String()
				}
			}
		}
	}

	return nil
}

func (m *model) loadBusinessDetail(id int) tea.Cmd {
	m.dash.businesses.loading = true
	return func() tea.Msg {
		b, err := m.api.getBusiness(id)
		if err != nil {
			return errMsg{err}
		}
		m.dash.businesses.detail = b
		m.dash.businesses.page = pageDetail
		m.dash.businesses.loading = false
		return nil
	}
}

func (m *model) createBusiness(idea string) tea.Cmd {
	return func() tea.Msg {
		b, err := m.api.createBusiness(idea)
		if err != nil {
			m.dash.businesses.creating = false
			return errMsg{err}
		}
		return businessCreatedMsg{b}
	}
}

func (m model) businessesView() string {
	var b strings.Builder

	switch m.dash.businesses.page {
	case pageList:
		b.WriteString(titleStyle.Render("Businesses"))
		b.WriteString("\n\n")
		b.WriteString(m.businessListView())
	case pageDetail:
		b.WriteString(m.businessDetailView())
	case pageCreate:
		b.WriteString(m.businessCreateView())
	}

	return b.String()
}

func (m model) businessListView() string {
	var b strings.Builder

	if m.dash.businesses.loading {
		b.WriteString(spinnerStyle.Render("Loading businesses..."))
		return b.String()
	}

	if len(m.dash.businesses.businesses) == 0 {
		b.WriteString(subtitleStyle.Render("No businesses yet. Press 'n' to create one."))
		b.WriteString("\n\n")
		b.WriteString(helpStyle.Render("n: create business • r: refresh • q: quit"))
		return b.String()
	}

	for i, biz := range m.dash.businesses.businesses {
		statusColor := special
		if biz.Status == "failed" || biz.Status == "error" {
			statusColor = warn
		} else if biz.Status == "in_progress" || biz.Status == "building" {
			statusColor = info
		}

		line := fmt.Sprintf("%s  %s  (%s)",
			statusStyle.Copy().BorderForeground(statusColor).Foreground(statusColor).Render(biz.Status),
			biz.Name,
			biz.CreatedAt[:10],
		)

		if i == m.dash.businesses.selected {
			b.WriteString(selectedItemStyle.Render("▸ " + line))
		} else {
			b.WriteString(itemStyle.Render("  " + line))
		}
		b.WriteString("\n")
	}

	b.WriteString("\n")
	b.WriteString(helpStyle.Render("↑/↓: navigate • enter: detail • n: create • r: refresh • q: quit"))

	return b.String()
}

func (m model) businessDetailView() string {
	var b strings.Builder
	d := m.dash.businesses.detail

	b.WriteString(titleStyle.Render(d.Name))
	b.WriteString("\n\n")

	statusColor := special
	switch d.Status {
	case "failed", "error":
		statusColor = warn
	case "in_progress", "building":
		statusColor = info
	}
	b.WriteString(statusStyle.Copy().BorderForeground(statusColor).Foreground(statusColor).Render("Status: " + d.Status))
	b.WriteString("\n\n")

	b.WriteString(detailStyle.Render(
		lipgloss.JoinVertical(lipgloss.Left,
			"Idea: "+d.Idea,
			"",
			"Description: "+d.Description,
			"",
			fmt.Sprintf("Progress: %d%%", d.Progress),
			"",
			"Created: "+d.CreatedAt,
			"Updated: "+d.UpdatedAt,
		),
	))
	b.WriteString("\n\n")

	if len(d.Agents) > 0 {
		b.WriteString(subtitleStyle.Render("Agent Status"))
		b.WriteString("\n")
		for _, agent := range d.Agents {
			agColor := subtle
			switch agent.Status {
			case "completed", "success":
				agColor = special
			case "in_progress", "running":
				agColor = info
			case "failed", "error":
				agColor = warn
			}
			b.WriteString(itemStyle.Copy().Foreground(agColor).Render("  • " + agent.Name + ": " + agent.Status))
			b.WriteString("\n")
		}
	}

	b.WriteString("\n")
	b.WriteString(helpStyle.Render("esc: back • q: quit"))

	return b.String()
}

func (m model) businessCreateView() string {
	var b strings.Builder

	b.WriteString(titleStyle.Render("Create New Business"))
	b.WriteString("\n\n")
	b.WriteString(subtitleStyle.Render("Enter your business idea below:"))
	b.WriteString("\n\n")

	inputBorder := subtle
	if m.dash.businesses.page == pageCreate {
		inputBorder = highlight
	}

	inputBox := lipgloss.NewStyle().
		Border(lipgloss.NormalBorder(), true, true, true, true).
		BorderForeground(inputBorder).
		Width(50).
		Height(3).
		Padding(0, 1).
		Render(m.dash.businesses.ideaInput + "█")

	b.WriteString(lipgloss.NewStyle().PaddingLeft(2).Render(inputBox))
	b.WriteString("\n\n")

	if m.dash.businesses.creating {
		b.WriteString(spinnerStyle.Render("Creating business..."))
	} else {
		b.WriteString(lipgloss.NewStyle().PaddingLeft(2).Render(
			"[ Press enter to submit ]",
		))
	}

	b.WriteString("\n\n")
	b.WriteString(helpStyle.Render("type: enter idea • enter: submit • esc: back"))

	return b.String()
}
