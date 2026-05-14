package api

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

const BaseURL = "http://localhost:8000/api/v1"

type Client struct {
	http      *http.Client
	Token     string
	UserEmail string
	UserName  string
	UserID    string
}

func New() *Client {
	return &Client{
		http: &http.Client{Timeout: 10 * time.Second},
	}
}

func (c *Client) do(method, path string, body any) (*http.Response, error) {
	var buf bytes.Buffer
	if body != nil {
		if err := json.NewEncoder(&buf).Encode(body); err != nil {
			return nil, err
		}
	}
	req, err := http.NewRequest(method, BaseURL+path, &buf)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	if c.Token != "" {
		req.Header.Set("Authorization", "Bearer "+c.Token)
	}
	return c.http.Do(req)
}

// ── Auth ──────────────────────────────────────────────────────────────────────

type AuthResponse struct {
	AccessToken string `json:"access_token"`
	UserID      string `json:"user_id"`
	Email       string `json:"email"`
	Name        string `json:"name"`
	Role        string `json:"role"`
}

func (c *Client) Login(email, password string) (*AuthResponse, error) {
	resp, err := c.do("POST", "/auth/login", map[string]string{
		"email": email, "password": password,
	})
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("login failed (%d)", resp.StatusCode)
	}
	var out AuthResponse
	return &out, json.NewDecoder(resp.Body).Decode(&out)
}

func (c *Client) Register(email, password, name string) (*AuthResponse, error) {
	resp, err := c.do("POST", "/auth/register", map[string]string{
		"email": email, "password": password, "name": name,
	})
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 && resp.StatusCode != 201 {
		return nil, fmt.Errorf("register failed (%d)", resp.StatusCode)
	}
	var out AuthResponse
	return &out, json.NewDecoder(resp.Body).Decode(&out)
}

// ── Businesses ────────────────────────────────────────────────────────────────

type Business struct {
	ID           string `json:"id"`
	Name         string `json:"name"`
	Description  string `json:"description"`
	Status       string `json:"status"`
	CurrentPhase string `json:"current_phase"`
	CreatedAt    string `json:"created_at"`
	UpdatedAt    string `json:"updated_at"`
}

func (c *Client) ListBusinesses() ([]Business, error) {
	resp, err := c.do("GET", "/businesses/", nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	var out []Business
	return out, json.NewDecoder(resp.Body).Decode(&out)
}

func (c *Client) GetBusiness(id string) (*Business, error) {
	resp, err := c.do("GET", "/businesses/"+id, nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	var out Business
	return &out, json.NewDecoder(resp.Body).Decode(&out)
}

func (c *Client) CreateBusiness(idea string) (*Business, error) {
	resp, err := c.do("POST", "/businesses/create", map[string]string{"idea": idea})
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 && resp.StatusCode != 201 {
		return nil, fmt.Errorf("create failed (%d)", resp.StatusCode)
	}
	var out Business
	return &out, json.NewDecoder(resp.Body).Decode(&out)
}

func (c *Client) DeleteBusiness(id string) error {
	resp, err := c.do("DELETE", "/businesses/"+id, nil)
	if err != nil {
		return err
	}
	resp.Body.Close()
	return nil
}

// ── Approvals ─────────────────────────────────────────────────────────────────

type Approval struct {
	ID          string `json:"id"`
	Title       string `json:"title"`
	Description string `json:"description"`
	Status      string `json:"status"`
	Urgency     string `json:"urgency"`
	CreatedAt   string `json:"created_at"`
}

func (c *Client) ListApprovals() ([]Approval, error) {
	resp, err := c.do("GET", "/approvals/", nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	var out []Approval
	return out, json.NewDecoder(resp.Body).Decode(&out)
}

func (c *Client) DecideApproval(id, decision string) error {
	body := map[string]string{
		"decision": decision,
		"ceo_id":   c.UserID,
	}
	resp, err := c.do("POST", "/approvals/"+id+"/decide", body)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return fmt.Errorf("decide failed (%d)", resp.StatusCode)
	}
	return nil
}

// ── Metrics ───────────────────────────────────────────────────────────────────

type Metric struct {
	ID             string  `json:"id"`
	BusinessID     string  `json:"business_id"`
	RecordedByRole string  `json:"recorded_by_role"`
	DailyRevenue   float64 `json:"daily_revenue"`
	UsersCount     int     `json:"users_count"`
	ChurnRate      float64 `json:"churn_rate"`
	CreatedAt      string  `json:"created_at"`
}

func (c *Client) ListMetrics(businessID string) ([]Metric, error) {
	path := "/metrics/"
	if businessID != "" {
		path += "?business_id=" + businessID
	}
	resp, err := c.do("GET", path, nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	var out []Metric
	return out, json.NewDecoder(resp.Body).Decode(&out)
}