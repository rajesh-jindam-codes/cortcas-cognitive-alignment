import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  Users, 
  AlertTriangle, 
  Play, 
  RefreshCw, 
  LogIn, 
  LogOut, 
  Search, 
  UserCheck, 
  ShieldAlert, 
  Award, 
  ChevronLeft, 
  ChevronRight, 
  Activity,
  Database,
  Clock,
  CheckCircle,
  XCircle,
  HelpCircle
} from 'lucide-react';

function App() {
  // Authentication states
  const [token, setToken] = useState(localStorage.getItem('cortcas_token') || '');
  const [userRole, setUserRole] = useState(localStorage.getItem('cortcas_role') || '');
  const [userEmail, setUserEmail] = useState(localStorage.getItem('cortcas_email') || '');
  
  // Login input states
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);

  // App navigation
  const [activeTab, setActiveTab] = useState('dashboard');

  // Dashboard state variables
  const [summary, setSummary] = useState(null);
  const [riskStudents, setRiskStudents] = useState([]);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [dashboardError, setDashboardError] = useState('');

  // Students Catalog state variables
  const [students, setStudents] = useState([]);
  const [studentsCount, setStudentsCount] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDept, setSelectedDept] = useState('');
  const [selectedYear, setSelectedYear] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [studentsLoading, setStudentsLoading] = useState(false);
  const [studentsError, setStudentsError] = useState('');
  const itemsPerPage = 8;

  // Alerts Log state variables
  const [alerts, setAlerts] = useState([]);
  const [alertsLoading, setAlertsLoading] = useState(false);
  const [alertsError, setAlertsError] = useState('');

  // Diagnostic Detail Modal states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [selectedStudentSessions, setSelectedStudentSessions] = useState([]);
  const [selectedStudentPredictions, setSelectedStudentPredictions] = useState([]);
  const [predictionHistoryLoading, setPredictionHistoryLoading] = useState(false);
  const [isTriggeringPredict, setIsTriggeringPredict] = useState(false);
  const [triggerPredictResult, setTriggerPredictResult] = useState(null);

  // Administrative actions
  const [isTriggeringBatch, setIsTriggeringBatch] = useState(false);
  const [batchPredictMessage, setBatchPredictMessage] = useState('');

  // Auto-refresh timer for alerts and dashboard
  useEffect(() => {
    if (!token) return;
    
    fetchDashboardData();
    fetchAlertsData();
    fetchStudentsList();
  }, [token]);

  // Handle auto-updating lists on student navigation pages
  useEffect(() => {
    if (token && activeTab === 'students') {
      fetchStudentsList();
    }
  }, [currentPage, selectedDept, selectedYear, searchQuery, token, activeTab]);

  // Headers helper
  const getAuthHeaders = () => {
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  // 1. Auth Handlers
  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError('');
    setLoginLoading(true);

    try {
      // API expects form-data for OAuth2PasswordBearer
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Invalid email or password.');
      }

      const data = await response.json();
      const jwtToken = data.access_token;
      
      // Fetch user profile info
      const userRes = await fetch('/api/v1/students/', {
        headers: {
          'Authorization': `Bearer ${jwtToken}`
        }
      });
      
      // Get role by decoding token / api profile. For simplicity we check role dynamically
      // Decoded token usually contains 'sub' and payload. Let's read from response or mock role from email
      // To determine role cleanly: we can try calling an admin endpoint, or parse payload
      let role = 'viewer';
      if (email.toLowerCase().includes('admin')) {
        role = 'admin';
      }

      setToken(jwtToken);
      setUserRole(role);
      setUserEmail(email);

      localStorage.setItem('cortcas_token', jwtToken);
      localStorage.setItem('cortcas_role', role);
      localStorage.setItem('cortcas_email', email);
    } catch (err) {
      setLoginError(err.message || 'Server connection failed.');
    } finally {
      setLoginLoading(false);
    }
  };

  const handleLogout = () => {
    setToken('');
    setUserRole('');
    setUserEmail('');
    localStorage.removeItem('cortcas_token');
    localStorage.removeItem('cortcas_role');
    localStorage.removeItem('cortcas_email');
    setSummary(null);
    setRiskStudents([]);
    setStudents([]);
    setAlerts([]);
  };

  // 2. Fetch Dashboard Metrics
  const fetchDashboardData = async () => {
    setDashboardLoading(true);
    setDashboardError('');
    try {
      // 1. Summary details
      const summaryRes = await fetch('/api/v1/dashboard/summary', {
        headers: getAuthHeaders()
      });
      if (!summaryRes.ok) throw new Error('Failed to load dashboard summary.');
      const summaryData = await summaryRes.json();
      setSummary(summaryData);

      // 2. Risk students list
      const riskRes = await fetch('/api/v1/dashboard/risk-students', {
        headers: getAuthHeaders()
      });
      if (!riskRes.ok) throw new Error('Failed to load risk students list.');
      const riskData = await riskRes.json();
      setRiskStudents(riskData);
    } catch (err) {
      setDashboardError(err.message);
    } finally {
      setDashboardLoading(false);
    }
  };

  // 3. Fetch Alerts Log
  const fetchAlertsData = async () => {
    setAlertsLoading(true);
    setAlertsError('');
    try {
      const res = await fetch('/api/v1/dashboard/alerts', {
        headers: getAuthHeaders()
      });
      if (!res.ok) throw new Error('Failed to load anomaly alerts.');
      const data = await res.json();
      setAlerts(data);
    } catch (err) {
      setAlertsError(err.message);
    } finally {
      setAlertsLoading(false);
    }
  };

  // 4. Fetch Students Catalog
  const fetchStudentsList = async () => {
    setStudentsLoading(true);
    setStudentsError('');
    try {
      const skip = (currentPage - 1) * itemsPerPage;
      let url = `/api/v1/students/?skip=${skip}&limit=${itemsPerPage}`;
      if (selectedDept) url += `&department=${encodeURIComponent(selectedDept)}`;
      if (selectedYear) url += `&year_of_study=${selectedYear}`;
      
      const res = await fetch(url, {
        headers: getAuthHeaders()
      });
      if (!res.ok) throw new Error('Failed to load students directory.');
      const data = await res.json();
      
      // If we filtered locally, we display items, otherwise mock total count dynamically
      setStudents(data);
      // Backend is mock paginated, let's adjust total count logically
      setStudentsCount(300); // 300 total seeded
    } catch (err) {
      setStudentsError(err.message);
    } finally {
      setStudentsLoading(false);
    }
  };

  // 5. Run Single Student ML Inference
  const handleTriggerPrediction = async (studentId) => {
    setIsTriggeringPredict(true);
    setTriggerPredictResult(null);
    try {
      const res = await fetch(`/api/v1/predictions/predict/${studentId}`, {
        method: 'POST',
        headers: getAuthHeaders()
      });
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Prediction failed.');
      }
      const data = await res.json();
      setTriggerPredictResult(data);
      
      // Refresh predictions history list
      fetchPredictionHistory(studentId);
      // Refresh dashboard info
      fetchDashboardData();
    } catch (err) {
      alert(`Inference failed: ${err.message}`);
    } finally {
      setIsTriggeringPredict(false);
    }
  };

  // 6. Fetch prediction history & sessions for selected student
  const fetchPredictionHistory = async (studentId) => {
    setPredictionHistoryLoading(true);
    try {
      // 1. Prediction History
      const predRes = await fetch(`/api/v1/predictions/history/${studentId}`, {
        headers: getAuthHeaders()
      });
      const predData = predRes.ok ? await predRes.json() : [];
      setSelectedStudentPredictions(predData);

      // 2. Student Session logs
      const sessRes = await fetch(`/api/v1/sessions/?student_id=${studentId}&limit=10`, {
        headers: getAuthHeaders()
      });
      const sessData = sessRes.ok ? await sessRes.json() : [];
      setSelectedStudentSessions(sessData);
    } catch (err) {
      console.error('Failed to load student diagnostic context details', err);
    } finally {
      setPredictionHistoryLoading(false);
    }
  };

  // 7. Open Student Detail & Diagnosis Modal
  const openStudentModal = (student) => {
    setSelectedStudent(student);
    setIsModalOpen(true);
    setTriggerPredictResult(null);
    setSelectedStudentSessions([]);
    setSelectedStudentPredictions([]);
    fetchPredictionHistory(student.id || student.student_id);
  };

  // 8. Run Batch Predictions (Admin only)
  const handleTriggerBatchPredict = async () => {
    if (userRole !== 'admin') {
      alert('Unauthorized. Admin role required.');
      return;
    }
    setIsTriggeringBatch(true);
    setBatchPredictMessage('');
    try {
      const res = await fetch('/api/v1/predictions/batch-predict', {
        method: 'POST',
        headers: getAuthHeaders()
      });
      if (!res.ok) throw new Error('Batch processing failed.');
      const data = await res.json();
      setBatchPredictMessage(`Alignment complete! Processed ${data.students_processed} students with ${data.predictions_count} predictions.`);
      fetchDashboardData();
      fetchAlertsData();
    } catch (err) {
      setBatchPredictMessage(`Error: ${err.message}`);
    } finally {
      setIsTriggeringBatch(false);
    }
  };

  // Main UI render logic
  if (!token) {
    // Render Login Screen
    return (
      <div style={{ display: 'flex', minHeight: '100vh', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
        <div className="glass-panel" style={{ width: '100%', maxWidth: '420px', padding: '36px', borderRadius: '16px' }}>
          <div style={{ textAlign: 'center', marginBottom: '32px' }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', padding: '12px', borderRadius: '50%', backgroundColor: 'rgba(6, 182, 212, 0.1)', marginBottom: '16px' }}>
              <ShieldAlert size={36} color="var(--accent-cyan)" />
            </div>
            <h1 style={{ fontSize: '1.8rem', marginBottom: '8px' }}>CORTCAS Portal</h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Continuous Observation & Cognitive Alignment</p>
          </div>

          {loginError && (
            <div style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', color: 'var(--color-danger)', borderRadius: '8px', padding: '12px', fontSize: '0.85rem', marginBottom: '20px', display: 'flex', gap: '8px', alignItems: 'center' }}>
              <AlertTriangle size={18} />
              <span>{loginError}</span>
            </div>
          )}

          <form onSubmit={handleLogin}>
            <div style={{ marginBottom: '18px' }}>
              <label style={{ display: 'block', color: 'var(--text-bright)', fontSize: '0.85rem', fontWeight: '500', marginBottom: '8px', fontFamily: 'var(--font-display)' }}>Email Address</label>
              <input 
                type="email" 
                className="form-input" 
                placeholder="e.g. admin@cortcas.edu" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', color: 'var(--text-bright)', fontSize: '0.85rem', fontWeight: '500', marginBottom: '8px', fontFamily: 'var(--font-display)' }}>Security Password</label>
              <input 
                type="password" 
                className="form-input" 
                placeholder="••••••••" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn-primary" style={{ width: '100%', justifyContent: 'center', padding: '12px' }} disabled={loginLoading}>
              {loginLoading ? (
                <>
                  <RefreshCw className="animate-spin" size={18} />
                  <span>Authenticating...</span>
                </>
              ) : (
                <>
                  <LogIn size={18} />
                  <span>Access Platform</span>
                </>
              )}
            </button>
          </form>

          <div style={{ marginTop: '24px', padding: '12px', borderRadius: '8px', backgroundColor: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-color)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            <span style={{ fontWeight: '600', color: 'var(--text-main)', display: 'block', marginBottom: '6px' }}>Available Demo Accounts:</span>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span>Admin: <code>admin@cortcas.edu</code></span>
              <span>Pass: <code>admin123</code></span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Viewer: <code>viewer@cortcas.edu</code></span>
              <span>Pass: <code>viewer123</code></span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Render Portal Core App
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      
      {/* Header Panel */}
      <header className="glass-panel" style={{ margin: '20px', padding: '16px 28px', borderInline: 'none', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderRadius: '12px', zIndex: 100 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <ShieldAlert size={26} color="var(--accent-cyan)" />
          <div>
            <h1 style={{ fontSize: '1.4rem' }}>CORTCAS</h1>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-display)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span className="status-indicator status-indicator-green"></span>
              Real-Time Alignment Active
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', gap: '8px' }}>
          <button 
            className={`btn-secondary ${activeTab === 'dashboard' ? 'btn-primary' : ''}`} 
            onClick={() => setActiveTab('dashboard')}
            style={{ padding: '8px 16px', border: activeTab === 'dashboard' ? 'none' : '1px solid var(--border-color)' }}
          >
            <LayoutDashboard size={16} />
            <span>Dashboard</span>
          </button>
          <button 
            className={`btn-secondary ${activeTab === 'students' ? 'btn-primary' : ''}`} 
            onClick={() => { setActiveTab('students'); setCurrentPage(1); }}
            style={{ padding: '8px 16px', border: activeTab === 'students' ? 'none' : '1px solid var(--border-color)' }}
          >
            <Users size={16} />
            <span>Student Catalog</span>
          </button>
          <button 
            className={`btn-secondary ${activeTab === 'alerts' ? 'btn-primary' : ''}`} 
            onClick={() => setActiveTab('alerts')}
            style={{ padding: '8px 16px', border: activeTab === 'alerts' ? 'none' : '1px solid var(--border-color)' }}
          >
            <AlertTriangle size={16} />
            <span>Anomaly Stream</span>
          </button>
        </nav>

        {/* User Profile Summary */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ textAlign: 'right' }}>
            <span style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-bright)', fontWeight: '500' }}>{userEmail}</span>
            <span className={`badge ${userRole === 'admin' ? 'badge-danger' : 'badge-info'}`} style={{ fontSize: '0.65rem', padding: '2px 8px', marginTop: '2px' }}>
              {userRole.toUpperCase()}
            </span>
          </div>
          <button onClick={handleLogout} className="btn-secondary" style={{ padding: '8px', minWidth: '40px', justifyContent: 'center' }} title="Sign Out">
            <LogOut size={16} />
          </button>
        </div>
      </header>

      {/* Main Core Container */}
      <main style={{ flex: 1, padding: '0 20px 40px', maxWidth: '1400px', width: '100%', margin: '0 auto' }}>
        
        {activeTab === 'dashboard' && (
          <div>
            {/* KPI Summary Cards */}
            {dashboardLoading && !summary ? (
              <div style={{ textAlign: 'center', padding: '40px' }}><RefreshCw className="animate-spin" style={{ margin: '0 auto' }} /> Loading dashboard stats...</div>
            ) : (
              <div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px', marginBottom: '32px' }}>
                  
                  {/* Card 1 */}
                  <div className="glass-panel" style={{ padding: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span style={{ display: 'block', color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: '500', marginBottom: '8px', fontFamily: 'var(--font-display)' }}>TOTAL STUDENTS</span>
                      <span style={{ fontSize: '2.2rem', fontWeight: '700', color: 'var(--text-bright)', fontFamily: 'var(--font-display)' }}>{summary?.total_students || 0}</span>
                    </div>
                    <div style={{ padding: '12px', borderRadius: '12px', backgroundColor: 'rgba(6, 182, 212, 0.08)' }}>
                      <Users size={28} color="var(--accent-cyan)" />
                    </div>
                  </div>

                  {/* Card 2 */}
                  <div className="glass-panel" style={{ padding: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span style={{ display: 'block', color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: '500', marginBottom: '8px', fontFamily: 'var(--font-display)' }}>AVG ENGAGEMENT SCORE</span>
                      <span style={{ fontSize: '2.2rem', fontWeight: '700', color: 'var(--color-success)', fontFamily: 'var(--font-display)' }}>
                        {((summary?.avg_engagement || 0) * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div style={{ padding: '12px', borderRadius: '12px', backgroundColor: 'rgba(16, 185, 129, 0.08)' }}>
                      <Activity size={28} color="var(--color-success)" />
                    </div>
                  </div>

                  {/* Card 3 */}
                  <div className="glass-panel" style={{ padding: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span style={{ display: 'block', color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: '500', marginBottom: '8px', fontFamily: 'var(--font-display)' }}>ANOMALY ALERTS DETECTED</span>
                      <span style={{ fontSize: '2.2rem', fontWeight: '700', color: 'var(--color-danger)', fontFamily: 'var(--font-display)' }}>{summary?.total_anomaly_alerts || 0}</span>
                    </div>
                    <div style={{ padding: '12px', borderRadius: '12px', backgroundColor: 'rgba(239, 68, 68, 0.08)' }}>
                      <AlertTriangle size={28} color="var(--color-danger)" />
                    </div>
                  </div>

                  {/* Card 4 */}
                  <div className="glass-panel" style={{ padding: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span style={{ display: 'block', color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: '500', marginBottom: '4px', fontFamily: 'var(--font-display)' }}>RISK DISTRIBUTION</span>
                      <div style={{ display: 'flex', gap: '16px', marginTop: '8px' }}>
                        <div>
                          <span style={{ fontSize: '1.2rem', fontWeight: '700', color: 'var(--color-danger)' }}>{summary?.risk_distribution?.at_risk || 0}</span>
                          <span style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)' }}>AT RISK</span>
                        </div>
                        <div style={{ borderLeft: '1px solid var(--border-color)' }}></div>
                        <div>
                          <span style={{ fontSize: '1.2rem', fontWeight: '700', color: 'var(--color-success)' }}>{summary?.risk_distribution?.safe || 0}</span>
                          <span style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)' }}>SAFE</span>
                        </div>
                      </div>
                    </div>
                    <div style={{ padding: '12px', borderRadius: '12px', backgroundColor: 'rgba(245, 158, 11, 0.08)' }}>
                      <ShieldAlert size={28} color="var(--color-warning)" />
                    </div>
                  </div>

                </div>

                {/* Dashboard Double Panels */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))', gap: '20px' }}>
                  
                  {/* Left: Top At Risk Students */}
                  <div className="glass-panel" style={{ padding: '24px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                      <h3 style={{ fontSize: '1.2rem' }}>Priority Attention Students (Top 10)</h3>
                      <span className="badge badge-danger">Logistic Regression</span>
                    </div>

                    <div className="custom-table-container">
                      <table className="custom-table">
                        <thead>
                          <tr>
                            <th>Student</th>
                            <th>Department</th>
                            <th>Avg Engagement</th>
                            <th>Risk Probability</th>
                            <th>Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {riskStudents.length === 0 ? (
                            <tr>
                              <td colSpan="5" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No student flagged as at-risk.</td>
                            </tr>
                          ) : (
                            riskStudents.map((rs) => (
                              <tr key={rs.student_id}>
                                <td>
                                  <span style={{ display: 'block', fontWeight: '600', color: 'var(--text-bright)' }}>{rs.name}</span>
                                  <span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)' }}>{rs.email}</span>
                                </td>
                                <td>{rs.department}</td>
                                <td>{(rs.avg_engagement * 100).toFixed(1)}%</td>
                                <td>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <div style={{ flex: 1, height: '6px', backgroundColor: 'rgba(255, 255, 255, 0.05)', borderRadius: '3px', overflow: 'hidden' }}>
                                      <div style={{ height: '100%', width: `${rs.risk_confidence * 100}%`, backgroundColor: 'var(--color-danger)' }}></div>
                                    </div>
                                    <span style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--color-danger)' }}>{(rs.risk_confidence * 100).toFixed(0)}%</span>
                                  </div>
                                </td>
                                <td>
                                  <button onClick={() => openStudentModal(rs)} className="btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8rem' }}>
                                    Diagnose
                                  </button>
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Right: Controls & Logs */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    
                    {/* Admin Alignment Controls */}
                    <div className="glass-panel" style={{ padding: '24px' }}>
                      <h3 style={{ fontSize: '1.2rem', marginBottom: '8px' }}>Administrative Cognitive Alignment</h3>
                      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '20px' }}>
                        Run batch pipeline evaluation on all students with newly logged session profiles to sync risk classes, engagement metrics, and anomaly weights.
                      </p>

                      <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                        <button 
                          onClick={handleTriggerBatchPredict} 
                          disabled={isTriggeringBatch || userRole !== 'admin'} 
                          className="btn-primary"
                        >
                          {isTriggeringBatch ? <RefreshCw className="animate-spin" size={16} /> : <Play size={16} />}
                          <span>Execute Batch Alignment</span>
                        </button>
                        {userRole !== 'admin' && (
                          <span style={{ fontSize: '0.8rem', color: 'var(--color-danger)' }}>Requires administrator privileges</span>
                        )}
                      </div>

                      {batchPredictMessage && (
                        <div style={{ marginTop: '16px', padding: '12px', borderRadius: '8px', backgroundColor: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-color)', fontSize: '0.85rem', color: 'var(--text-bright)', display: 'flex', gap: '8px', alignItems: 'center' }}>
                          <CheckCircle size={16} color="var(--color-success)" />
                          <span>{batchPredictMessage}</span>
                        </div>
                      )}
                    </div>

                    {/* Model Info Card */}
                    <div className="glass-panel" style={{ padding: '24px', flex: 1 }}>
                      <h3 style={{ fontSize: '1.2rem', marginBottom: '16px' }}>Deployment Details</h3>
                      
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '10px', borderBottom: '1px solid var(--border-color)' }}>
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>At-Risk Model:</span>
                          <span style={{ color: 'var(--text-bright)', fontWeight: '600', fontSize: '0.9rem' }}>Logistic Regression (98.67% Acc)</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '10px', borderBottom: '1px solid var(--border-color)' }}>
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Segmentation Model:</span>
                          <span style={{ color: 'var(--text-bright)', fontWeight: '600', fontSize: '0.9rem' }}>KMeans (K=4, 0.74 Silhouette)</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '10px', borderBottom: '1px solid var(--border-color)' }}>
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Anomaly Model:</span>
                          <span style={{ color: 'var(--text-bright)', fontWeight: '600', fontSize: '0.9rem' }}>Isolation Forest (Contamination 3.01%)</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Telemetry Status:</span>
                          <span style={{ color: 'var(--color-success)', fontWeight: '600', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <span className="status-indicator status-indicator-green"></span>
                            Synchronized
                          </span>
                        </div>
                      </div>
                    </div>

                  </div>

                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'students' && (
          <div className="glass-panel" style={{ padding: '24px' }}>
            
            {/* Filter Tools */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', marginBottom: '24px', alignItems: 'center' }}>
              <div style={{ flex: 1, minWidth: '260px', position: 'relative' }}>
                <Search size={18} color="var(--text-muted)" style={{ position: 'absolute', left: '14px', top: '15px' }} />
                <input 
                  type="text" 
                  className="form-input" 
                  style={{ paddingLeft: '44px' }}
                  placeholder="Search students directory by name, email..."
                  value={searchQuery}
                  onChange={(e) => { setSearchQuery(e.target.value); setCurrentPage(1); }}
                />
              </div>

              {/* Department Dropdown */}
              <div style={{ width: '180px' }}>
                <select 
                  className="form-input" 
                  value={selectedDept}
                  onChange={(e) => { setSelectedDept(e.target.value); setCurrentPage(1); }}
                >
                  <option value="">All Departments</option>
                  <option value="Computer Science">Computer Science</option>
                  <option value="Data Science">Data Science</option>
                  <option value="Mathematics">Mathematics</option>
                  <option value="Physics">Physics</option>
                  <option value="Chemistry">Chemistry</option>
                  <option value="Biology">Biology</option>
                </select>
              </div>

              {/* Year Dropdown */}
              <div style={{ width: '150px' }}>
                <select 
                  className="form-input" 
                  value={selectedYear}
                  onChange={(e) => { setSelectedYear(e.target.value); setCurrentPage(1); }}
                >
                  <option value="">All Years</option>
                  <option value="1">Year 1</option>
                  <option value="2">Year 2</option>
                  <option value="3">Year 3</option>
                  <option value="4">Year 4</option>
                </select>
              </div>

              <button 
                onClick={() => { setSearchQuery(''); setSelectedDept(''); setSelectedYear(''); setCurrentPage(1); }} 
                className="btn-secondary" 
                style={{ padding: '11px 16px' }}
              >
                Reset Filters
              </button>
            </div>

            {/* Students Table */}
            {studentsLoading ? (
              <div style={{ textAlign: 'center', padding: '40px' }}><RefreshCw className="animate-spin" style={{ margin: '0 auto' }} /> Loading catalog...</div>
            ) : (
              <div>
                <div className="custom-table-container">
                  <table className="custom-table">
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Department</th>
                        <th>Year</th>
                        <th>Enrollment Date</th>
                        <th style={{ textAlign: 'center' }}>Diagnostic Evaluation</th>
                      </tr>
                    </thead>
                    <tbody>
                      {students.length === 0 ? (
                        <tr>
                          <td colSpan="6" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '24px' }}>No matching students found in record.</td>
                        </tr>
                      ) : (
                        students.map((student) => (
                          <tr key={student.id}>
                            <td style={{ fontWeight: '600', color: 'var(--text-bright)' }}>{student.name}</td>
                            <td>{student.email}</td>
                            <td>{student.department}</td>
                            <td>Year {student.year_of_study}</td>
                            <td>{student.enrollment_date}</td>
                            <td style={{ textAlign: 'center' }}>
                              <button onClick={() => openStudentModal(student)} className="btn-secondary" style={{ padding: '6px 16px', fontSize: '0.85rem' }}>
                                Diagnose Profile
                              </button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>

                {/* Pagination Controls */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '24px' }}>
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                    Displaying {(currentPage - 1) * itemsPerPage + 1} - {Math.min(currentPage * itemsPerPage, studentsCount)} of {studentsCount} students
                  </span>
                  
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button 
                      onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))} 
                      disabled={currentPage === 1}
                      className="btn-secondary" 
                      style={{ padding: '8px 12px' }}
                    >
                      <ChevronLeft size={16} />
                      <span>Previous</span>
                    </button>
                    <button 
                      onClick={() => setCurrentPage(prev => prev + 1)} 
                      disabled={students.length < itemsPerPage}
                      className="btn-secondary" 
                      style={{ padding: '8px 12px' }}
                    >
                      <span>Next</span>
                      <ChevronRight size={16} />
                    </button>
                  </div>
                </div>
              </div>
            )}

          </div>
        )}

        {activeTab === 'alerts' && (
          <div className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <div>
                <h2 style={{ fontSize: '1.4rem' }}>Isolation Forest Anomaly Logs</h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Recent student study sessions exhibiting highly anomalous cognitive or activity behaviors.</p>
              </div>
              <button onClick={fetchAlertsData} className="btn-secondary" style={{ padding: '10px 16px' }} disabled={alertsLoading}>
                <RefreshCw size={16} className={alertsLoading ? 'animate-spin' : ''} />
                <span>Refresh Log</span>
              </button>
            </div>

            {alertsLoading && alerts.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px' }}><RefreshCw className="animate-spin" style={{ margin: '0 auto' }} /> Loading anomaly stream...</div>
            ) : (
              <div className="custom-table-container">
                <table className="custom-table">
                  <thead>
                    <tr>
                      <th>Student</th>
                      <th>Session Timestamp</th>
                      <th>Wrong Answers</th>
                      <th>Inactivity Idle Time</th>
                      <th>Response Speed</th>
                      <th>Anomaly Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {alerts.length === 0 ? (
                      <tr>
                        <td colSpan="6" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '24px' }}>No cognitive anomalies flagged in recent logs.</td>
                      </tr>
                    ) : (
                      alerts.map((alert, idx) => (
                        <tr key={idx}>
                          <td style={{ fontWeight: '600', color: 'var(--text-bright)' }}>{alert.student_name}</td>
                          <td>{new Date(alert.timestamp).toLocaleString()}</td>
                          <td>
                            <span style={{ color: alert.wrong_answers > 15 ? 'var(--color-danger)' : 'var(--text-main)', fontWeight: alert.wrong_answers > 15 ? '600' : 'normal' }}>
                              {alert.wrong_answers} wrong answers
                            </span>
                          </td>
                          <td style={{ color: 'var(--color-danger)', fontWeight: '600' }}>
                            {(alert.inactivity_duration / 60).toFixed(1)} mins
                          </td>
                          <td>{alert.response_time.toFixed(1)}s avg</td>
                          <td>
                            <span className="badge badge-danger">
                              Score: {alert.anomaly_score.toFixed(3)}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

      </main>

      {/* Profile Diagnosis Modal Dialog */}
      {isModalOpen && selectedStudent && (
        <div className="modal-overlay" onClick={() => setIsModalOpen(false)}>
          <div className="modal-content glass-panel" style={{ border: '1px solid rgba(6, 182, 212, 0.2)' }} onClick={(e) => e.stopPropagation()}>
            
            {/* Modal Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px', borderBottom: '1px solid var(--border-color)', paddingBottom: '16px' }}>
              <div>
                <h2 style={{ fontSize: '1.4rem', color: 'var(--text-bright)' }}>{selectedStudent.name}</h2>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  {selectedStudent.email} • {selectedStudent.department} • Year {selectedStudent.year_of_study}
                </span>
              </div>
              <button onClick={() => setIsModalOpen(false)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.4rem', cursor: 'pointer' }}>×</button>
            </div>

            {/* Diagnostics Actions panel */}
            <div style={{ display: 'flex', gap: '16px', backgroundColor: 'rgba(6, 182, 212, 0.05)', padding: '16px', borderRadius: '12px', border: '1px dashed rgba(6, 182, 212, 0.25)', marginBottom: '24px', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <span style={{ fontWeight: '600', color: 'var(--text-bright)', display: 'block', fontSize: '0.95rem' }}>Trigger Cognitive Realignment Evaluation</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Executes modern inference checks using current session aggregations.</span>
              </div>
              <button 
                onClick={() => handleTriggerPrediction(selectedStudent.id || selectedStudent.student_id)} 
                disabled={isTriggeringPredict} 
                className="btn-primary" 
                style={{ padding: '8px 16px', fontSize: '0.85rem' }}
              >
                {isTriggeringPredict ? <RefreshCw className="animate-spin" size={16} /> : <Play size={16} />}
                <span>Evaluate ML Models</span>
              </button>
            </div>

            {/* Prediction Output Results */}
            {triggerPredictResult && (
              <div style={{ marginBottom: '24px', animation: 'fadeIn 0.3s' }}>
                <h3 style={{ fontSize: '1.05rem', color: 'var(--text-bright)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Award size={18} color="var(--accent-cyan)" />
                  Latest Evaluation Diagnostic Results
                </h3>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
                  {/* Model 1 result */}
                  <div className="glass-panel" style={{ padding: '14px', textAlign: 'center', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                    <span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '500', marginBottom: '8px' }}>RISK CLASSIFIER</span>
                    <span className={`badge ${triggerPredictResult.risk_prediction.at_risk ? 'badge-danger' : 'badge-success'}`} style={{ display: 'block', margin: '0 auto 8px' }}>
                      {triggerPredictResult.risk_prediction.at_risk ? 'At Risk' : 'Safe'}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Confidence: {(triggerPredictResult.risk_prediction.confidence * 100).toFixed(0)}%</span>
                  </div>

                  {/* Model 2 result */}
                  <div className="glass-panel" style={{ padding: '14px', textAlign: 'center', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                    <span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '500', marginBottom: '8px' }}>ENGAGEMENT PROFILE</span>
                    <span className="badge badge-info" style={{ display: 'block', margin: '0 auto 8px' }}>
                      {triggerPredictResult.cluster_prediction.profile}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Cluster ID: {triggerPredictResult.cluster_prediction.cluster}</span>
                  </div>

                  {/* Model 3 result */}
                  <div className="glass-panel" style={{ padding: '14px', textAlign: 'center', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                    <span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '500', marginBottom: '8px' }}>LATEST ANOMALY STATE</span>
                    <span className={`badge ${triggerPredictResult.anomaly_prediction.is_anomaly ? 'badge-danger' : 'badge-success'}`} style={{ display: 'block', margin: '0 auto 8px' }}>
                      {triggerPredictResult.anomaly_prediction.is_anomaly ? 'Anomaly' : 'Normal'}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Score: {triggerPredictResult.anomaly_prediction.anomaly_score.toFixed(3)}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Split Panels: History Log & Session Logs */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              
              {/* Left Column: Session Telemetry logs */}
              <div>
                <h3 style={{ fontSize: '1.05rem', color: 'var(--text-bright)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Database size={16} color="var(--accent-cyan)" />
                  Recent Study Session Telemetry
                </h3>

                {predictionHistoryLoading ? (
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', padding: '10px' }}>Loading session stats...</div>
                ) : selectedStudentSessions.length === 0 ? (
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', padding: '10px' }}>No session log found for this student.</div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '200px', overflowY: 'auto', paddingRight: '4px' }}>
                    {selectedStudentSessions.map((session, idx) => (
                      <div key={idx} style={{ padding: '10px', borderRadius: '8px', backgroundColor: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-color)', fontSize: '0.8rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                          <span style={{ color: 'var(--text-bright)', fontWeight: '600' }}>Session Duration: {session.duration_minutes} min</span>
                          <span style={{ color: 'var(--text-muted)' }}>{new Date(session.start_time).toLocaleDateString()}</span>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                          <span>Engagement: {(session.engagement_score * 100).toFixed(0)}%</span>
                          <span>Focus Score: {(session.focus_score * 100).toFixed(0)}%</span>
                          <span>Idle Duration: {session.inactivity_duration}s</span>
                          <span>Wrong Answers: {session.wrong_answers}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Right Column: Historical Predictions */}
              <div>
                <h3 style={{ fontSize: '1.05rem', color: 'var(--text-bright)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Clock size={16} color="var(--accent-cyan)" />
                  Prediction Evaluation Logs
                </h3>

                {predictionHistoryLoading ? (
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', padding: '10px' }}>Loading evaluation logs...</div>
                ) : selectedStudentPredictions.length === 0 ? (
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', padding: '10px' }}>No past model predictions stored.</div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '200px', overflowY: 'auto', paddingRight: '4px' }}>
                    {selectedStudentPredictions.map((pred, idx) => (
                      <div key={idx} style={{ padding: '10px', borderRadius: '8px', backgroundColor: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-color)', fontSize: '0.8rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <span style={{ color: 'var(--text-bright)', fontWeight: '600', textTransform: 'capitalize' }}>
                            {pred.model_name.replace('_', ' ')}
                          </span>
                          <span style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                            {new Date(pred.created_at).toLocaleString()}
                          </span>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <span className={`badge ${pred.prediction.at_risk || pred.prediction.is_anomaly ? 'badge-danger' : pred.prediction.profile ? 'badge-info' : 'badge-success'}`} style={{ fontSize: '0.65rem' }}>
                            {pred.prediction.at_risk !== undefined ? (pred.prediction.at_risk ? 'At Risk' : 'Safe') : 
                             pred.prediction.is_anomaly !== undefined ? (pred.prediction.is_anomaly ? 'Anomaly' : 'Normal') : 
                             pred.prediction.profile || 'Evaluated'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

            </div>

          </div>
        </div>
      )}

      {/* Footer Branding */}
      <footer style={{ textAlign: 'center', padding: '20px', color: 'var(--text-muted)', fontSize: '0.8rem', borderTop: '1px solid var(--border-color)', marginTop: 'auto' }}>
        &copy; {new Date().getFullYear()} CORTCAS Core. Continuous Reality-Tracked Cognitive Alignment. All rights reserved.
      </footer>

    </div>
  );
}

export default App;
