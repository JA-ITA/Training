import React, { useState, useEffect, createContext, useContext } from 'react';
import axios from 'axios';
import { Plus, FileText, Video, Image, Music, Trash2, Edit, ChevronDown, ChevronRight, Upload, GraduationCap, Users, Award, BarChart3, Settings, LogOut, BookOpen, ClipboardList, UserPlus, CheckCircle, Timer, Target, Eye, Play, Download, Certificate, Shield, PlayCircle, Pause, Volume2, Maximize, Minimize } from 'lucide-react';
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Input } from './components/ui/input';
import { Textarea } from './components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Separator } from './components/ui/separator';
import { Alert, AlertDescription } from './components/ui/alert';
import { Label } from './components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './components/ui/collapsible';
import { Checkbox } from './components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from './components/ui/radio-group';
import { Progress } from './components/ui/progress';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Create Auth Context
const AuthContext = createContext();

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Auth Provider Component
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      // Set axios default header
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      // Verify token and get user info
      axios.get(`${API_BASE_URL}/api/me`)
        .then(response => {
          setUser(response.data);
        })
        .catch(() => {
          // Token invalid, clear it
          logout();
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = async (username, password) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/login`, {
        username,
        password
      });
      
      const { access_token, user: userData } = response.data;
      setToken(access_token);
      setUser(userData);
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      };
    }
  };

  const register = async (userData) => {
    try {
      await axios.post(`${API_BASE_URL}/api/register`, userData);
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Registration failed' 
      };
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Login Component
const LoginForm = ({ onToggleMode }) => {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await login(credentials.username, credentials.password);
    
    if (!result.success) {
      setError(result.error);
    }
    
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <GraduationCap className="h-8 w-8 text-blue-600" />
            <span className="text-2xl font-bold text-gray-900">ITA Training</span>
          </div>
          <CardTitle>Welcome Back</CardTitle>
          <CardDescription>Sign in to your training dashboard</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                value={credentials.username}
                onChange={(e) => setCredentials(prev => ({ ...prev, username: e.target.value }))}
                placeholder="Enter your username"
                required
              />
            </div>
            
            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={credentials.password}
                onChange={(e) => setCredentials(prev => ({ ...prev, password: e.target.value }))}
                placeholder="Enter your password"
                required
              />
            </div>

            {error && (
              <Alert className="border-red-200 bg-red-50">
                <AlertDescription className="text-red-800">{error}</AlertDescription>
              </Alert>
            )}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Don't have an account?{' '}
              <button
                onClick={onToggleMode}
                className="text-blue-600 hover:text-blue-500 font-medium"
              >
                Sign up
              </button>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Register Component
const RegisterForm = ({ onToggleMode }) => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    role: 'learner'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const { register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    const result = await register(formData);
    
    if (result.success) {
      setSuccess('Registration successful! You can now sign in.');
      setFormData({
        username: '',
        email: '',
        password: '',
        full_name: '',
        role: 'learner'
      });
    } else {
      setError(result.error);
    }
    
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <GraduationCap className="h-8 w-8 text-blue-600" />
            <span className="text-2xl font-bold text-gray-900">ITA Training</span>
          </div>
          <CardTitle>Create Account</CardTitle>
          <CardDescription>Join our training platform</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="full_name">Full Name</Label>
              <Input
                id="full_name"
                type="text"
                value={formData.full_name}
                onChange={(e) => setFormData(prev => ({ ...prev, full_name: e.target.value }))}
                placeholder="Enter your full name"
                required
              />
            </div>

            <div>
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                value={formData.username}
                onChange={(e) => setFormData(prev => ({ ...prev, username: e.target.value }))}
                placeholder="Choose a username"
                required
              />
            </div>
            
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                placeholder="Enter your email"
                required
              />
            </div>
            
            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                placeholder="Create a password"
                required
              />
            </div>

            <div>
              <Label htmlFor="role">Role</Label>
              <Select value={formData.role} onValueChange={(value) => setFormData(prev => ({ ...prev, role: value }))}>
                <SelectTrigger>
                  <SelectValue placeholder="Select your role" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="learner">Learner</SelectItem>
                  <SelectItem value="instructor">Instructor</SelectItem>
                  <SelectItem value="admin">Administrator</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {error && (
              <Alert className="border-red-200 bg-red-50">
                <AlertDescription className="text-red-800">{error}</AlertDescription>
              </Alert>
            )}

            {success && (
              <Alert className="border-green-200 bg-green-50">
                <AlertDescription className="text-green-800">{success}</AlertDescription>
              </Alert>
            )}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Creating Account...' : 'Create Account'}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Already have an account?{' '}
              <button
                onClick={onToggleMode}
                className="text-blue-600 hover:text-blue-500 font-medium"
              >
                Sign in
              </button>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Auth Container
const AuthContainer = () => {
  const [isLogin, setIsLogin] = useState(true);
  
  return isLogin ? 
    <LoginForm onToggleMode={() => setIsLogin(false)} /> : 
    <RegisterForm onToggleMode={() => setIsLogin(true)} />;
};

// Main App Component
function MainApp() {
  const { user, logout } = useAuth();
  const [programs, setPrograms] = useState([]);
  const [selectedProgram, setSelectedProgram] = useState(null);
  const [programStructure, setProgramStructure] = useState(null);
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Assessment states
  const [questions, setQuestions] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [selectedAssessment, setSelectedAssessment] = useState(null);
  const [assessmentQuestions, setAssessmentQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [assessmentResults, setAssessmentResults] = useState(null);

  // Certificate states
  const [certificates, setCertificates] = useState([]);
  const [selectedCertificate, setSelectedCertificate] = useState(null);
  const [verificationCode, setVerificationCode] = useState('');
  const [verificationResult, setVerificationResult] = useState(null);

  // Content viewing states
  const [selectedContent, setSelectedContent] = useState(null);
  const [contentProgress, setContentProgress] = useState({});
  const [programProgress, setProgramProgress] = useState(null);

  // Form states
  const [programForm, setProgramForm] = useState({
    title: '',
    description: '',
    learning_objectives: [''],
    expiry_duration: 12,
    renewal_requirements: ''
  });

  const [moduleForm, setModuleForm] = useState({
    title: '',
    description: '',
    order: 1
  });

  const [unitForm, setUnitForm] = useState({
    title: '',
    learning_objectives: [''],
    order: 1
  });

  const [questionForm, setQuestionForm] = useState({
    question_text: '',
    question_type: 'multiple_choice',
    options: [{ text: '', is_correct: false }, { text: '', is_correct: false }],
    correct_answer: '',
    points: 1,
    explanation: ''
  });

  const [assessmentForm, setAssessmentForm] = useState({
    title: '',
    description: '',
    program_id: '',
    module_id: '',
    unit_id: '',
    question_ids: [],
    pass_mark: 80,
    time_limit: null,
    max_attempts: 3,
    randomize_questions: false
  });

  const [expandedModules, setExpandedModules] = useState(new Set());

  useEffect(() => {
    fetchPrograms();
    if (user && (user.role === 'admin' || user.role === 'instructor')) {
      fetchQuestions();
      fetchAssessments();
    }
    if (user) {
      fetchCertificates();
    }
  }, [user]);

  const fetchPrograms = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/programs`);
      setPrograms(response.data);
    } catch (err) {
      setError('Failed to fetch programs');
    } finally {
      setLoading(false);
    }
  };

  const fetchProgramStructure = async (programId) => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/programs/${programId}/structure`);
      setProgramStructure(response.data);
    } catch (err) {
      setError('Failed to fetch program structure');
    } finally {
      setLoading(false);
    }
  };

  const fetchQuestions = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/questions`);
      setQuestions(response.data);
    } catch (err) {
      setError('Failed to fetch questions');
    }
  };

  const fetchAssessments = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/assessments`);
      setAssessments(response.data);
    } catch (err) {
      setError('Failed to fetch assessments');
    }
  };

  const fetchCertificates = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/certificates`);
      setCertificates(response.data);
    } catch (err) {
      setError('Failed to fetch certificates');
    }
  };

  const fetchContentProgress = async (contentId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/content/${contentId}/progress`);
      setContentProgress(prev => ({
        ...prev,
        [contentId]: response.data
      }));
    } catch (err) {
      console.log('Failed to fetch content progress');
    }
  };

  const updateContentProgress = async (contentId, progressData) => {
    try {
      await axios.post(`${API_BASE_URL}/api/content/${contentId}/progress`, progressData);
      fetchContentProgress(contentId);
    } catch (err) {
      console.log('Failed to update content progress');
    }
  };

  const fetchProgramProgress = async (programId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/programs/${programId}/progress`);
      setProgramProgress(response.data);
    } catch (err) {
      setError('Failed to fetch program progress');
    }
  };

  const verifyCertificate = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE_URL}/api/certificates/verify`, {
        verification_code: verificationCode
      });
      setVerificationResult(response.data);
    } catch (err) {
      setError('Failed to verify certificate');
    } finally {
      setLoading(false);
    }
  };

  const downloadCertificate = async (certificateId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/certificates/${certificateId}/download`, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `certificate_${certificateId}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to download certificate');
    }
  };

  const createProgram = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const payload = {
        ...programForm,
        learning_objectives: programForm.learning_objectives.filter(obj => obj.trim() !== '')
      };
      
      await axios.post(`${API_BASE_URL}/api/programs`, payload);
      setSuccess('Program created successfully!');
      setProgramForm({
        title: '',
        description: '',
        learning_objectives: [''],
        expiry_duration: 12,
        renewal_requirements: ''
      });
      fetchPrograms();
    } catch (err) {
      setError('Failed to create program');
    } finally {
      setLoading(false);
    }
  };

  const createQuestion = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      let payload = { ...questionForm };
      
      // Clean up based on question type
      if (payload.question_type === 'true_false') {
        payload.options = [];
      } else if (payload.question_type === 'essay') {
        payload.options = [];
        payload.correct_answer = null;
      }
      
      await axios.post(`${API_BASE_URL}/api/questions`, payload);
      setSuccess('Question created successfully!');
      setQuestionForm({
        question_text: '',
        question_type: 'multiple_choice',
        options: [{ text: '', is_correct: false }, { text: '', is_correct: false }],
        correct_answer: '',
        points: 1,
        explanation: ''
      });
      fetchQuestions();
    } catch (err) {
      setError('Failed to create question');
    } finally {
      setLoading(false);
    }
  };

  const createAssessment = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      await axios.post(`${API_BASE_URL}/api/assessments`, assessmentForm);
      setSuccess('Assessment created successfully!');
      setAssessmentForm({
        title: '',
        description: '',
        program_id: '',
        module_id: '',
        unit_id: '',
        question_ids: [],
        pass_mark: 80,
        time_limit: null,
        max_attempts: 3,
        randomize_questions: false
      });
      fetchAssessments();
    } catch (err) {
      setError('Failed to create assessment');
    } finally {
      setLoading(false);
    }
  };

  const startAssessment = async (assessmentId) => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/assessments/${assessmentId}/questions`);
      setAssessmentQuestions(response.data);
      setCurrentQuestionIndex(0);
      setAnswers({});
      setAssessmentResults(null);
      
      const assessment = assessments.find(a => a.id === assessmentId);
      setSelectedAssessment(assessment);
      setCurrentPage('take_assessment');
    } catch (err) {
      setError('Failed to start assessment');
    } finally {
      setLoading(false);
    }
  };

  const submitAssessment = async () => {
    try {
      setLoading(true);
      const submission = {
        assessment_id: selectedAssessment.id,
        answers: Object.entries(answers).map(([questionId, answer]) => ({
          question_id: questionId,
          selected_option_id: answer.selected_option_id || null,
          answer_text: answer.answer_text || null
        }))
      };
      
      const response = await axios.post(`${API_BASE_URL}/api/assessments/${selectedAssessment.id}/submit`, submission);
      setAssessmentResults(response.data);
      
      // If certificate was generated, fetch certificates
      if (response.data.certificate_generated) {
        setSuccess('Congratulations! You have earned a certificate for completing this program!');
        fetchCertificates();
      }
      
      setCurrentPage('assessment_results');
    } catch (err) {
      setError('Failed to submit assessment');
    } finally {
      setLoading(false);
    }
  };

  const addObjectiveField = (setter, currentObjectives) => {
    setter(prev => ({
      ...prev,
      learning_objectives: [...currentObjectives, '']
    }));
  };

  const updateObjective = (setter, index, value, currentObjectives) => {
    const newObjectives = [...currentObjectives];
    newObjectives[index] = value;
    setter(prev => ({
      ...prev,
      learning_objectives: newObjectives
    }));
  };

  const removeObjective = (setter, index, currentObjectives) => {
    const newObjectives = currentObjectives.filter((_, i) => i !== index);
    setter(prev => ({
      ...prev,
      learning_objectives: newObjectives.length > 0 ? newObjectives : ['']
    }));
  };

  const addQuestionOption = () => {
    setQuestionForm(prev => ({
      ...prev,
      options: [...prev.options, { text: '', is_correct: false }]
    }));
  };

  const updateQuestionOption = (index, field, value) => {
    setQuestionForm(prev => ({
      ...prev,
      options: prev.options.map((option, i) => 
        i === index ? { ...option, [field]: value } : option
      )
    }));
  };

  const removeQuestionOption = (index) => {
    setQuestionForm(prev => ({
      ...prev,
      options: prev.options.filter((_, i) => i !== index)
    }));
  };

  const toggleModuleExpansion = (moduleId) => {
    const newExpanded = new Set(expandedModules);
    if (newExpanded.has(moduleId)) {
      newExpanded.delete(moduleId);
    } else {
      newExpanded.add(moduleId);
    }
    setExpandedModules(newExpanded);
  };

  const getContentIcon = (contentType) => {
    switch (contentType) {
      case 'pdf':
      case 'document':
        return <FileText className="h-4 w-4" />;
      case 'video':
        return <Video className="h-4 w-4" />;
      case 'image':
        return <Image className="h-4 w-4" />;
      case 'audio':
        return <Music className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  // Enhanced Content Viewer Component
  const ContentViewer = ({ content, onClose }) => {
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [isFullscreen, setIsFullscreen] = useState(false);

    const handleProgressUpdate = (progressData) => {
      updateContentProgress(content.id, progressData);
    };

    const handleVideoProgress = (e) => {
      const video = e.target;
      const progress = (video.currentTime / video.duration) * 100;
      
      setCurrentTime(video.currentTime);
      
      // Update progress every 10 seconds or on significant progress changes
      if (Math.floor(video.currentTime) % 10 === 0) {
        handleProgressUpdate({
          progress_percentage: Math.round(progress),
          last_position: video.currentTime,
          time_spent: video.currentTime,
          completed: progress >= 95
        });
      }
    };

    const handleVideoEnd = () => {
      handleProgressUpdate({
        progress_percentage: 100,
        last_position: duration,
        time_spent: duration,
        completed: true
      });
      setIsPlaying(false);
    };

    const formatTime = (seconds) => {
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const contentUrl = `${API_BASE_URL}/api/content/${content.id}/stream`;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
        <div className={`bg-white rounded-lg max-w-6xl w-full mx-4 ${isFullscreen ? 'h-full' : 'max-h-[90vh]'} overflow-hidden`}>
          <div className="p-4 border-b flex items-center justify-between">
            <h3 className="text-lg font-semibold">{content.title}</h3>
            <div className="flex items-center gap-2">
              {content.content_type === 'video' && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsFullscreen(!isFullscreen)}
                >
                  {isFullscreen ? <Minimize className="h-4 w-4" /> : <Maximize className="h-4 w-4" />}
                </Button>
              )}
              <Button variant="outline" size="sm" onClick={onClose}>
                ×
              </Button>
            </div>
          </div>
          
          <div className="p-4 flex-1 overflow-auto">
            {content.content_type === 'video' && (
              <div className="relative">
                <video
                  src={contentUrl}
                  className="w-full rounded-lg"
                  controls
                  onTimeUpdate={handleVideoProgress}
                  onEnded={handleVideoEnd}
                  onLoadedMetadata={(e) => setDuration(e.target.duration)}
                >
                  Your browser does not support the video tag.
                </video>
                
                {/* Progress indicator */}
                <div className="mt-4">
                  <div className="flex justify-between text-sm text-gray-600 mb-2">
                    <span>Progress: {contentProgress[content.id]?.progress_percentage || 0}%</span>
                    <span>{formatTime(currentTime)} / {formatTime(duration)}</span>
                  </div>
                  <Progress 
                    value={contentProgress[content.id]?.progress_percentage || 0} 
                    className="w-full"
                  />
                </div>
              </div>
            )}

            {content.content_type === 'audio' && (
              <div className="text-center py-8">
                <Music className="h-16 w-16 mx-auto text-gray-400 mb-4" />
                <audio
                  src={contentUrl}
                  className="w-full"
                  controls
                  onTimeUpdate={handleVideoProgress}
                  onEnded={handleVideoEnd}
                  onLoadedMetadata={(e) => setDuration(e.target.duration)}
                >
                  Your browser does not support the audio tag.
                </audio>
                
                <div className="mt-4">
                  <div className="flex justify-between text-sm text-gray-600 mb-2">
                    <span>Progress: {contentProgress[content.id]?.progress_percentage || 0}%</span>
                    <span>{formatTime(currentTime)} / {formatTime(duration)}</span>
                  </div>
                  <Progress 
                    value={contentProgress[content.id]?.progress_percentage || 0} 
                    className="w-full"
                  />
                </div>
              </div>
            )}

            {content.content_type === 'pdf' && (
              <div className="text-center py-8">
                <FileText className="h-16 w-16 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-600 mb-4">PDF Viewer</p>
                <iframe
                  src={contentUrl}
                  className="w-full h-96 border rounded-lg"
                  title={content.title}
                />
                <Button
                  className="mt-4"
                  onClick={() => {
                    handleProgressUpdate({
                      progress_percentage: 100,
                      completed: true,
                      time_spent: 300 // Assume 5 minutes for PDF
                    });
                  }}
                >
                  Mark as Complete
                </Button>
              </div>
            )}

            {content.content_type === 'image' && (
              <div className="text-center">
                <img
                  src={contentUrl}
                  alt={content.title}
                  className="max-w-full h-auto rounded-lg mx-auto"
                  onLoad={() => {
                    handleProgressUpdate({
                      progress_percentage: 100,
                      completed: true,
                      time_spent: 30 // Assume 30 seconds for image
                    });
                  }}
                />
              </div>
            )}

            {(!['video', 'audio', 'pdf', 'image'].includes(content.content_type)) && (
              <div className="text-center py-8">
                <FileText className="h-16 w-16 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-600 mb-4">Document: {content.title}</p>
                <Button
                  onClick={() => window.open(contentUrl, '_blank')}
                  className="mr-2"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    handleProgressUpdate({
                      progress_percentage: 100,
                      completed: true,
                      time_spent: 180 // Assume 3 minutes for document
                    });
                  }}
                >
                  Mark as Complete
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  // Dashboard View
  const DashboardView = () => (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Training Management Dashboard</h1>
        <p className="text-gray-600 mt-2">Transportation of Hazardous Materials Training Program Administration</p>
        <div className="mt-2">
          <Badge variant="outline" className="mr-2">
            {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
          </Badge>
          <span className="text-sm text-gray-600">Welcome, {user.full_name}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="border-l-4 border-l-blue-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">Total Programs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">{programs.length}</div>
            <p className="text-sm text-gray-600">Active training programs</p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-green-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">Questions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{questions.length}</div>
            <p className="text-sm text-gray-600">Question bank</p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-orange-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">Assessments</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-600">{assessments.length}</div>
            <p className="text-sm text-gray-600">Active assessments</p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-purple-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">My Role</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600 capitalize">{user.role}</div>
            <p className="text-sm text-gray-600">Access level</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Recent Programs</CardTitle>
            <CardDescription>Latest training programs available</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {programs.slice(0, 5).map((program) => (
                <div key={program.id} className="flex items-center justify-between p-3 rounded-lg border">
                  <div>
                    <h4 className="font-medium">{program.title}</h4>
                    <p className="text-sm text-gray-600">{program.description.substring(0, 60)}...</p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSelectedProgram(program);
                      fetchProgramStructure(program.id);
                      setCurrentPage('programs');
                    }}
                  >
                    View
                  </Button>
                </div>
              ))}
              {programs.length === 0 && (
                <p className="text-gray-500 text-center py-4">No programs available yet</p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Get started with common tasks</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(user.role === 'admin' || user.role === 'instructor') && (
                <>
                  <Button
                    className="w-full justify-start"
                    variant="outline"
                    onClick={() => setCurrentPage('programs')}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Create New Program
                  </Button>
                  <Button
                    className="w-full justify-start"
                    variant="outline"
                    onClick={() => setCurrentPage('questions')}
                  >
                    <BookOpen className="h-4 w-4 mr-2" />
                    Manage Questions
                  </Button>
                  <Button
                    className="w-full justify-start"
                    variant="outline"
                    onClick={() => setCurrentPage('assessments')}
                  >
                    <ClipboardList className="h-4 w-4 mr-2" />
                    Create Assessment
                  </Button>
                </>
              )}
              {user.role === 'learner' && (
                <>
                  <Button
                    className="w-full justify-start"
                    variant="outline"
                    onClick={() => setCurrentPage('programs')}
                  >
                    <GraduationCap className="h-4 w-4 mr-2" />
                    Browse Programs
                  </Button>
                  <Button
                    className="w-full justify-start"
                    variant="outline"
                    onClick={() => setCurrentPage('assessments')}
                  >
                    <ClipboardList className="h-4 w-4 mr-2" />
                    Take Assessment
                  </Button>
                </>
              )}
              {user.role === 'admin' && (
                <Button
                  className="w-full justify-start"
                  variant="outline"
                  onClick={() => setCurrentPage('users')}
                >
                  <Users className="h-4 w-4 mr-2" />
                  Manage Users
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  // Assessment Taking View
  const AssessmentTakingView = () => {
    if (!selectedAssessment || !assessmentQuestions.length) {
      return <div>Loading assessment...</div>;
    }

    const currentQuestion = assessmentQuestions[currentQuestionIndex];
    const isLastQuestion = currentQuestionIndex === assessmentQuestions.length - 1;
    const totalQuestions = assessmentQuestions.length;

    const handleAnswer = (questionId, answer) => {
      setAnswers(prev => ({
        ...prev,
        [questionId]: answer
      }));
    };

    const nextQuestion = () => {
      if (currentQuestionIndex < assessmentQuestions.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
      }
    };

    const prevQuestion = () => {
      if (currentQuestionIndex > 0) {
        setCurrentQuestionIndex(currentQuestionIndex - 1);
      }
    };

    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>{selectedAssessment.title}</CardTitle>
                <CardDescription>{selectedAssessment.description}</CardDescription>
              </div>
              <Badge variant="outline">
                {currentQuestionIndex + 1} of {totalQuestions}
              </Badge>
            </div>
            <Progress value={(currentQuestionIndex + 1) / totalQuestions * 100} className="mt-4" />
          </CardHeader>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium mb-4">
                  Question {currentQuestionIndex + 1}: {currentQuestion.question_text}
                </h3>
                
                {currentQuestion.question_type === 'multiple_choice' && (
                  <RadioGroup
                    value={answers[currentQuestion.id]?.selected_option_id || ''}
                    onValueChange={(value) => handleAnswer(currentQuestion.id, { selected_option_id: value })}
                  >
                    {currentQuestion.options.map((option) => (
                      <div key={option.id} className="flex items-center space-x-2">
                        <RadioGroupItem value={option.id} id={option.id} />
                        <Label htmlFor={option.id}>{option.text}</Label>
                      </div>
                    ))}
                  </RadioGroup>
                )}

                {currentQuestion.question_type === 'true_false' && (
                  <RadioGroup
                    value={answers[currentQuestion.id]?.answer_text || ''}
                    onValueChange={(value) => handleAnswer(currentQuestion.id, { answer_text: value })}
                  >
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="true" id="true" />
                      <Label htmlFor="true">True</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="false" id="false" />
                      <Label htmlFor="false">False</Label>
                    </div>
                  </RadioGroup>
                )}

                {currentQuestion.question_type === 'essay' && (
                  <Textarea
                    value={answers[currentQuestion.id]?.answer_text || ''}
                    onChange={(e) => handleAnswer(currentQuestion.id, { answer_text: e.target.value })}
                    placeholder="Type your answer here..."
                    rows={6}
                  />
                )}
              </div>

              <div className="flex items-center justify-between pt-4 border-t">
                <Button
                  variant="outline"
                  onClick={prevQuestion}
                  disabled={currentQuestionIndex === 0}
                >
                  Previous
                </Button>

                <div className="space-x-2">
                  {!isLastQuestion ? (
                    <Button onClick={nextQuestion}>
                      Next
                    </Button>
                  ) : (
                    <Button 
                      onClick={submitAssessment}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      Submit Assessment
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  // Assessment Results View
  const AssessmentResultsView = () => {
    if (!assessmentResults) {
      return <div>Loading results...</div>;
    }

    const { percentage, is_passed, total_points, earned_points } = assessmentResults;

    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <Card>
          <CardHeader className="text-center">
            <div className="flex items-center justify-center mb-4">
              {is_passed ? (
                <CheckCircle className="h-16 w-16 text-green-500" />
              ) : (
                <div className="h-16 w-16 rounded-full bg-red-100 flex items-center justify-center">
                  <span className="text-red-500 text-2xl font-bold">✗</span>
                </div>
              )}
            </div>
            <CardTitle className={is_passed ? 'text-green-600' : 'text-red-600'}>
              {is_passed ? 'Congratulations!' : 'Assessment Not Passed'}
            </CardTitle>
            <CardDescription>
              {is_passed 
                ? 'You have successfully completed the assessment.'
                : 'You did not meet the minimum pass mark. Please review and try again.'
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-blue-600">{percentage.toFixed(1)}%</div>
                <p className="text-sm text-gray-600">Score</p>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">{earned_points}</div>
                <p className="text-sm text-gray-600">Points Earned</p>
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-600">{total_points}</div>
                <p className="text-sm text-gray-600">Total Points</p>
              </div>
              <div>
                <div className="text-2xl font-bold text-purple-600">{selectedAssessment?.pass_mark}%</div>
                <p className="text-sm text-gray-600">Pass Mark</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="text-center">
          <Button
            onClick={() => {
              setCurrentPage('assessments');
              setAssessmentResults(null);
              setSelectedAssessment(null);
            }}
          >
            Back to Assessments
          </Button>
        </div>
      </div>
    );
  };

  // Questions Management View
  const QuestionsView = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Question Bank</h1>
          <p className="text-gray-600 mt-2">Create and manage assessment questions</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Create New Question</CardTitle>
            <CardDescription>Add questions to your question bank</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={createQuestion} className="space-y-4">
              <div>
                <Label htmlFor="question_text">Question Text</Label>
                <Textarea
                  id="question_text"
                  value={questionForm.question_text}
                  onChange={(e) => setQuestionForm(prev => ({ ...prev, question_text: e.target.value }))}
                  placeholder="Enter your question"
                  required
                />
              </div>

              <div>
                <Label>Question Type</Label>
                <Select 
                  value={questionForm.question_type} 
                  onValueChange={(value) => setQuestionForm(prev => ({ ...prev, question_type: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="multiple_choice">Multiple Choice</SelectItem>
                    <SelectItem value="true_false">True/False</SelectItem>
                    <SelectItem value="essay">Essay</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {questionForm.question_type === 'multiple_choice' && (
                <div>
                  <Label>Answer Options</Label>
                  {questionForm.options.map((option, index) => (
                    <div key={index} className="flex items-center gap-2 mt-2">
                      <Input
                        value={option.text}
                        onChange={(e) => updateQuestionOption(index, 'text', e.target.value)}
                        placeholder={`Option ${index + 1}`}
                      />
                      <Checkbox
                        checked={option.is_correct}
                        onCheckedChange={(checked) => updateQuestionOption(index, 'is_correct', checked)}
                      />
                      <Label className="text-sm">Correct</Label>
                      {questionForm.options.length > 2 && (
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => removeQuestionOption(index)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  ))}
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={addQuestionOption}
                    className="mt-2"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Option
                  </Button>
                </div>
              )}

              {questionForm.question_type === 'true_false' && (
                <div>
                  <Label>Correct Answer</Label>
                  <Select 
                    value={questionForm.correct_answer} 
                    onValueChange={(value) => setQuestionForm(prev => ({ ...prev, correct_answer: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select correct answer" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="true">True</SelectItem>
                      <SelectItem value="false">False</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="points">Points</Label>
                  <Input
                    id="points"
                    type="number"
                    value={questionForm.points}
                    onChange={(e) => setQuestionForm(prev => ({ ...prev, points: parseInt(e.target.value) }))}
                    min="1"
                    required
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="explanation">Explanation (Optional)</Label>
                <Textarea
                  id="explanation"
                  value={questionForm.explanation}
                  onChange={(e) => setQuestionForm(prev => ({ ...prev, explanation: e.target.value }))}
                  placeholder="Explain the correct answer"
                />
              </div>

              <Button type="submit" disabled={loading}>
                {loading ? 'Creating...' : 'Create Question'}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Question Bank ({questions.length})</CardTitle>
            <CardDescription>Manage your existing questions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {questions.map((question) => (
                <div key={question.id} className="p-4 border rounded-lg">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="font-medium">{question.question_text}</p>
                      <div className="flex gap-2 mt-2">
                        <Badge variant="secondary" className="capitalize">
                          {question.question_type.replace('_', ' ')}
                        </Badge>
                        <Badge variant="outline">
                          {question.points} {question.points === 1 ? 'point' : 'points'}
                        </Badge>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="outline" size="sm">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
              {questions.length === 0 && (
                <p className="text-gray-500 text-center py-8">No questions created yet</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  // Assessments Management View
  const AssessmentsView = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Assessments</h1>
          <p className="text-gray-600 mt-2">
            {user.role === 'learner' ? 'Take assessments and view your results' : 'Create and manage assessments'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {(user.role === 'admin' || user.role === 'instructor') && (
          <Card>
            <CardHeader>
              <CardTitle>Create New Assessment</CardTitle>
              <CardDescription>Build assessments from your question bank</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={createAssessment} className="space-y-4">
                <div>
                  <Label htmlFor="title">Assessment Title</Label>
                  <Input
                    id="title"
                    value={assessmentForm.title}
                    onChange={(e) => setAssessmentForm(prev => ({ ...prev, title: e.target.value }))}
                    placeholder="Enter assessment title"
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={assessmentForm.description}
                    onChange={(e) => setAssessmentForm(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Assessment description"
                    required
                  />
                </div>

                <div>
                  <Label>Select Questions</Label>
                  <div className="space-y-2 max-h-40 overflow-y-auto border rounded p-2">
                    {questions.map((question) => (
                      <div key={question.id} className="flex items-center space-x-2">
                        <Checkbox
                          id={question.id}
                          checked={assessmentForm.question_ids.includes(question.id)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setAssessmentForm(prev => ({
                                ...prev,
                                question_ids: [...prev.question_ids, question.id]
                              }));
                            } else {
                              setAssessmentForm(prev => ({
                                ...prev,
                                question_ids: prev.question_ids.filter(id => id !== question.id)
                              }));
                            }
                          }}
                        />
                        <Label htmlFor={question.id} className="text-sm">
                          {question.question_text.substring(0, 60)}...
                        </Label>
                      </div>
                    ))}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    Selected: {assessmentForm.question_ids.length} questions
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="pass_mark">Pass Mark (%)</Label>
                    <Input
                      id="pass_mark"
                      type="number"
                      value={assessmentForm.pass_mark}
                      onChange={(e) => setAssessmentForm(prev => ({ ...prev, pass_mark: parseInt(e.target.value) }))}
                      min="1"
                      max="100"
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="max_attempts">Max Attempts</Label>
                    <Input
                      id="max_attempts"
                      type="number"
                      value={assessmentForm.max_attempts}
                      onChange={(e) => setAssessmentForm(prev => ({ ...prev, max_attempts: parseInt(e.target.value) }))}
                      min="1"
                      required
                    />
                  </div>
                </div>

                <Button type="submit" disabled={loading || assessmentForm.question_ids.length === 0}>
                  {loading ? 'Creating...' : 'Create Assessment'}
                </Button>
              </form>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle>
              {user.role === 'learner' ? 'Available Assessments' : `All Assessments (${assessments.length})`}
            </CardTitle>
            <CardDescription>
              {user.role === 'learner' ? 'Click to start an assessment' : 'Manage your assessments'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {assessments.map((assessment) => (
                <div key={assessment.id} className="p-4 border rounded-lg">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="font-medium">{assessment.title}</h4>
                      <p className="text-sm text-gray-600 mt-1">{assessment.description}</p>
                      <div className="flex gap-2 mt-2">
                        <Badge variant="outline">
                          {assessment.question_ids.length} questions
                        </Badge>
                        <Badge variant="outline">
                          {assessment.pass_mark}% pass mark
                        </Badge>
                        <Badge variant="outline">
                          {assessment.max_attempts} attempts
                        </Badge>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {user.role === 'learner' ? (
                        <Button 
                          size="sm"
                          onClick={() => startAssessment(assessment.id)}
                        >
                          <Play className="h-4 w-4 mr-2" />
                          Start
                        </Button>
                      ) : (
                        <>
                          <Button variant="outline" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="outline" size="sm">
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button variant="outline" size="sm">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              {assessments.length === 0 && (
                <p className="text-gray-500 text-center py-8">No assessments available yet</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  // Enhanced Programs View with Content Viewing
  const ProgramsView = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Training Programs</h1>
          <p className="text-gray-600 mt-2">
            {user.role === 'learner' ? 'Browse and access your training programs' : 'Create and manage training programs'}
          </p>
        </div>
      </div>

      {/* Program Structure View */}
      {programStructure && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>{programStructure.program.title}</CardTitle>
                <CardDescription>{programStructure.program.description}</CardDescription>
              </div>
              <Button 
                variant="outline"
                onClick={() => fetchProgramProgress(programStructure.program.id)}
              >
                View Progress
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {programStructure.modules.map((module) => (
                <div key={module.id} className="border rounded-lg p-4">
                  <Collapsible 
                    open={expandedModules.has(module.id)}
                    onOpenChange={() => toggleModuleExpansion(module.id)}
                  >
                    <CollapsibleTrigger className="flex items-center justify-between w-full text-left">
                      <div className="flex items-center space-x-2">
                        {expandedModules.has(module.id) ? 
                          <ChevronDown className="h-4 w-4" /> : 
                          <ChevronRight className="h-4 w-4" />
                        }
                        <h3 className="font-medium">{module.title}</h3>
                      </div>
                    </CollapsibleTrigger>
                    
                    <CollapsibleContent className="mt-4 space-y-3">
                      {module.units.map((unit) => (
                        <div key={unit.id} className="ml-6 p-3 bg-gray-50 rounded-lg">
                          <h4 className="font-medium text-sm">{unit.title}</h4>
                          
                          {/* Unit Content */}
                          <div className="mt-2 space-y-2">
                            {/* Fetch and display content for this unit */}
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={async () => {
                                try {
                                  const response = await axios.get(`${API_BASE_URL}/api/units/${unit.id}/content`);
                                  const contentItems = response.data;
                                  
                                  // Show content items
                                  unit.contentItems = contentItems;
                                  setExpandedModules(new Set(expandedModules)); // Trigger re-render
                                } catch (err) {
                                  setError('Failed to load content');
                                }
                              }}
                              className="text-xs"
                            >
                              Load Content ({unit.contentItems?.length || 0} items)
                            </Button>
                            
                            {unit.contentItems && unit.contentItems.map((content) => (
                              <div key={content.id} className="flex items-center justify-between p-2 bg-white rounded border">
                                <div className="flex items-center space-x-2">
                                  {getContentIcon(content.content_type)}
                                  <span className="text-sm">{content.title}</span>
                                  {contentProgress[content.id]?.completed && (
                                    <CheckCircle className="h-4 w-4 text-green-500" />
                                  )}
                                </div>
                                <div className="flex items-center gap-2">
                                  {contentProgress[content.id] && (
                                    <div className="text-xs text-gray-500">
                                      {contentProgress[content.id].progress_percentage}%
                                    </div>
                                  )}
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => {
                                      setSelectedContent(content);
                                      fetchContentProgress(content.id);
                                    }}
                                  >
                                    <Play className="h-4 w-4 mr-1" />
                                    View
                                  </Button>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </CollapsibleContent>
                  </Collapsible>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Programs List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {programs.map((program) => (
          <Card key={program.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="text-lg">{program.title}</CardTitle>
              <CardDescription>{program.description.substring(0, 100)}...</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <GraduationCap className="h-4 w-4 text-blue-500" />
                  <span className="text-sm text-gray-600">
                    {program.learning_objectives.length} Learning Objectives
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Timer className="h-4 w-4 text-orange-500" />
                  <span className="text-sm text-gray-600">
                    Valid for {program.expiry_duration} months
                  </span>
                </div>
                
                <div className="flex gap-2 mt-4">
                  <Button
                    size="sm"
                    onClick={() => {
                      setSelectedProgram(program);
                      fetchProgramStructure(program.id);
                    }}
                    className="flex-1"
                  >
                    View Program
                  </Button>
                  {user.role === 'learner' && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => fetchProgramProgress(program.id)}
                    >
                      Progress
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
        
        {programs.length === 0 && (
          <div className="col-span-full text-center py-12">
            <BookOpen className="h-16 w-16 mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">No programs available yet</p>
          </div>
        )}
      </div>

      {/* Content Viewer Modal */}
      {selectedContent && (
        <ContentViewer 
          content={selectedContent}
          onClose={() => setSelectedContent(null)}
        />
      )}

      {/* Program Progress Modal */}
      {programProgress && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-4xl mx-4 max-h-[80vh] overflow-auto">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Program Progress</CardTitle>
                <Button variant="ghost" size="sm" onClick={() => setProgramProgress(null)}>
                  ×
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {programProgress.modules.map((module) => (
                  <div key={module.module_id} className="border rounded-lg p-4">
                    <h4 className="font-medium mb-3">{module.module_title}</h4>
                    <div className="space-y-2">
                      {module.units.map((unit) => (
                        <div key={unit.unit_id} className="bg-gray-50 rounded p-3">
                          <h5 className="text-sm font-medium mb-2">{unit.unit_title}</h5>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                            {unit.content_items.map((content) => (
                              <div key={content.content_id} className="flex items-center justify-between p-2 bg-white rounded border text-sm">
                                <div className="flex items-center gap-2">
                                  {getContentIcon(content.content_type)}
                                  <span>{content.content_title}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                  {content.completed ? (
                                    <CheckCircle className="h-4 w-4 text-green-500" />
                                  ) : (
                                    <div className="text-xs text-gray-500">
                                      {content.progress_percentage}%
                                    </div>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );

  // Certificates Management View
  const CertificatesView = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Certificates</h1>
          <p className="text-gray-600 mt-2">View and download your earned certificates</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>My Certificates ({certificates.length})</CardTitle>
            <CardDescription>Certificates you have earned</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {certificates.map((certificate) => (
                <div key={certificate.id} className="p-4 border rounded-lg bg-gradient-to-r from-blue-50 to-indigo-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Award className="h-5 w-5 text-yellow-500" />
                        <h4 className="font-medium">{certificate.program_title}</h4>
                      </div>
                      <p className="text-sm text-gray-600">Issued to: {certificate.user_name}</p>
                      <p className="text-sm text-gray-600">Date: {new Date(certificate.issued_date).toLocaleDateString()}</p>
                      <div className="flex gap-2 mt-2">
                        <Badge variant="outline" className="text-xs">
                          #{certificate.certificate_number}
                        </Badge>
                        {certificate.is_valid ? (
                          <Badge variant="default" className="text-xs bg-green-100 text-green-800">
                            <Shield className="h-3 w-3 mr-1" />
                            Valid
                          </Badge>
                        ) : (
                          <Badge variant="destructive" className="text-xs">
                            Revoked
                          </Badge>
                        )}
                        {certificate.expiry_date && (
                          <Badge variant="outline" className="text-xs">
                            Expires: {new Date(certificate.expiry_date).toLocaleDateString()}
                          </Badge>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button 
                        size="sm"
                        onClick={() => downloadCertificate(certificate.id)}
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => setSelectedCertificate(certificate)}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
              {certificates.length === 0 && (
                <div className="text-center py-8">
                  <Award className="h-16 w-16 mx-auto text-gray-300 mb-4" />
                  <p className="text-gray-500">No certificates earned yet</p>
                  <p className="text-sm text-gray-400 mt-2">Complete training programs to earn certificates</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Certificate Verification</CardTitle>
            <CardDescription>Verify the authenticity of a certificate</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <Label htmlFor="verification_code">Verification Code</Label>
                <Input
                  id="verification_code"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value)}
                  placeholder="Enter verification code"
                />
              </div>
              
              <Button 
                onClick={verifyCertificate}
                disabled={loading || !verificationCode}
                className="w-full"
              >
                {loading ? 'Verifying...' : 'Verify Certificate'}
              </Button>

              {verificationResult && (
                <div className={`p-4 rounded-lg border ${
                  verificationResult.valid 
                    ? 'bg-green-50 border-green-200' 
                    : 'bg-red-50 border-red-200'
                }`}>
                  <div className="flex items-center gap-2 mb-2">
                    {verificationResult.valid ? (
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    ) : (
                      <div className="h-5 w-5 rounded-full bg-red-100 flex items-center justify-center">
                        <span className="text-red-600 text-xs font-bold">×</span>
                      </div>
                    )}
                    <span className={`font-medium ${
                      verificationResult.valid ? 'text-green-800' : 'text-red-800'
                    }`}>
                      {verificationResult.valid ? 'Certificate Valid' : 'Certificate Invalid'}
                    </span>
                  </div>
                  <p className={`text-sm ${
                    verificationResult.valid ? 'text-green-700' : 'text-red-700'
                  }`}>
                    {verificationResult.message}
                  </p>
                  
                  {verificationResult.valid && verificationResult.certificate && (
                    <div className="mt-4 p-3 bg-white rounded border">
                      <h5 className="font-medium">{verificationResult.certificate.program_title}</h5>
                      <p className="text-sm text-gray-600">Issued to: {verificationResult.certificate.user_name}</p>
                      <p className="text-sm text-gray-600">Date: {new Date(verificationResult.certificate.issued_date).toLocaleDateString()}</p>
                      <p className="text-sm text-gray-600">Certificate #: {verificationResult.certificate.certificate_number}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Certificate Detail Modal */}
      {selectedCertificate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-2xl mx-4">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Certificate Details</CardTitle>
                <Button variant="ghost" size="sm" onClick={() => setSelectedCertificate(null)}>
                  ×
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="text-center p-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg">
                  <Award className="h-16 w-16 mx-auto text-yellow-500 mb-4" />
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Certificate of Completion</h3>
                  <p className="text-lg text-gray-700">This certifies that</p>
                  <p className="text-2xl font-bold text-blue-600 my-4">{selectedCertificate.user_name}</p>
                  <p className="text-lg text-gray-700">has successfully completed</p>
                  <p className="text-xl font-semibold text-gray-900 mt-2">{selectedCertificate.program_title}</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-600">Certificate Number:</span>
                    <p className="text-gray-900">{selectedCertificate.certificate_number}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-600">Issued Date:</span>
                    <p className="text-gray-900">{new Date(selectedCertificate.issued_date).toLocaleDateString()}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-600">Verification Code:</span>
                    <p className="text-gray-900 font-mono">{selectedCertificate.verification_code}</p>
                  </div>
                  {selectedCertificate.expiry_date && (
                    <div>
                      <span className="font-medium text-gray-600">Valid Until:</span>
                      <p className="text-gray-900">{new Date(selectedCertificate.expiry_date).toLocaleDateString()}</p>
                    </div>
                  )}
                </div>
                
                <div className="flex gap-2 pt-4">
                  <Button 
                    onClick={() => downloadCertificate(selectedCertificate.id)}
                    className="flex-1"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download PDF
                  </Button>
                  <Button 
                    variant="outline"
                    onClick={() => {
                      navigator.clipboard.writeText(selectedCertificate.verification_code);
                      setSuccess('Verification code copied to clipboard');
                    }}
                  >
                    Copy Verification Code
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <GraduationCap className="h-8 w-8 text-blue-600" />
                <span className="text-xl font-bold text-gray-900">ITA Training</span>
              </div>
            </div>
            
            <nav className="hidden md:flex items-center space-x-8">
              <button
                onClick={() => setCurrentPage('dashboard')}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  currentPage === 'dashboard' 
                    ? 'bg-blue-100 text-blue-700' 
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setCurrentPage('programs')}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  currentPage === 'programs' 
                    ? 'bg-blue-100 text-blue-700' 
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Programs
              </button>
              <button
                onClick={() => setCurrentPage('assessments')}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  currentPage === 'assessments' 
                    ? 'bg-blue-100 text-blue-700' 
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Assessments
              </button>
              <button
                onClick={() => setCurrentPage('certificates')}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  currentPage === 'certificates' 
                    ? 'bg-blue-100 text-blue-700' 
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Certificates
              </button>
              {(user.role === 'admin' || user.role === 'instructor') && (
                <button
                  onClick={() => setCurrentPage('questions')}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    currentPage === 'questions' 
                      ? 'bg-blue-100 text-blue-700' 
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Questions
                </button>
              )}
              {user.role === 'admin' && (
                <button
                  onClick={() => setCurrentPage('users')}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    currentPage === 'users' 
                      ? 'bg-blue-100 text-blue-700' 
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Users
                </button>
              )}
            </nav>

            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600">
                {user.full_name} ({user.role})
              </div>
              <Button variant="ghost" size="sm" onClick={logout}>
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Alerts */}
        {error && (
          <Alert className="mb-6 border-red-200 bg-red-50">
            <AlertDescription className="text-red-800">{error}</AlertDescription>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setError('')}
              className="absolute right-2 top-2"
            >
              ×
            </Button>
          </Alert>
        )}
        
        {success && (
          <Alert className="mb-6 border-green-200 bg-green-50">
            <AlertDescription className="text-green-800">{success}</AlertDescription>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSuccess('')}
              className="absolute right-2 top-2"
            >
              ×
            </Button>
          </Alert>
        )}

        {/* Page Content */}
        {currentPage === 'dashboard' && <DashboardView />}
        {currentPage === 'programs' && <ProgramsView />}
        {currentPage === 'questions' && <QuestionsView />}
        {currentPage === 'assessments' && <AssessmentsView />}
        {currentPage === 'certificates' && <CertificatesView />}
        {currentPage === 'take_assessment' && <AssessmentTakingView />}
        {currentPage === 'assessment_results' && <AssessmentResultsView />}
      </main>
    </div>
  );
}

// Main App Component with Auth
function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

// App Content Component
function AppContent() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="spinner mb-4"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  return user ? <MainApp /> : <AuthContainer />;
}

export default App;