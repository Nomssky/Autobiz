package main

type appState int

const (
	stateLogin appState = iota
	stateRegister
	stateDashboard
)

type user struct {
	AccessToken string `json:"access_token"`
	TokenType   string `json:"token_type"`
	UserID      string `json:"user_id"`
	Email       string `json:"email"`
	Name        string `json:"name"`
	Role        string `json:"role"`
}

type business struct {
	ID          string `json:"id"`
	Name        string `json:"name"`
	Description string `json:"description"`
	Status      string `json:"status"`
	CurrentPhase string `json:"current_phase"`
	CreatedAt   string `json:"created_at"`
	UpdatedAt   string `json:"updated_at"`
}

type approvalRequest struct {
	ID           string `json:"id"`
	BusinessID   string `json:"business_id"`
	Title        string `json:"title"`
	Description  string `json:"description"`
	Urgency      string `json:"urgency"`
	Status       string `json:"status"`
	CreatedAt    string `json:"created_at"`
}

type metricSnapshot struct {
	ID              string  `json:"id"`
	BusinessID      string  `json:"business_id"`
	RecordedByRole  string  `json:"recorded_by_role"`
	DailyRevenue    float64 `json:"daily_revenue"`
	UsersCount      int     `json:"users_count"`
	ChurnRate       float64 `json:"churn_rate"`
	CreatedAt       string  `json:"created_at"`
}

type tab int

const (
	tabDashboard tab = iota
	tabBusinesses
	tabApprovals
	tabMetrics
)

type page int

const (
	pageList page = iota
	pageDetail
	pageCreate
)

type errMsg struct{ err error }

func (e errMsg) Error() string { return e.err.Error() }

type successMsg struct{ message string }

type loggedInMsg struct{ user user }

type businessesLoadedMsg struct{ businesses []business }

type businessCreatedMsg struct{ business business }

type approvalsLoadedMsg struct{ approvals []approvalRequest }

type metricsLoadedMsg struct{ metrics []metricSnapshot }
