import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Plus, FileText, Video, Image, Music, Trash2, Edit, ChevronDown, ChevronRight, Upload, GraduationCap, Users, Award, BarChart3, Settings, LogOut } from 'lucide-react';
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
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [programs, setPrograms] = useState([]);
  const [selectedProgram, setSelectedProgram] = useState(null);
  const [programStructure, setProgramStructure] = useState(null);
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

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

  const [expandedModules, setExpandedModules] = useState(new Set());

  useEffect(() => {
    fetchPrograms();
  }, []);

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

  const createModule = async (programId, moduleData) => {
    try {
      setLoading(true);
      await axios.post(`${API_BASE_URL}/api/modules`, {
        ...moduleData,
        program_id: programId
      });
      setSuccess('Module created successfully!');
      fetchProgramStructure(programId);
    } catch (err) {
      setError('Failed to create module');
    } finally {
      setLoading(false);
    }
  };

  const createUnit = async (moduleId, unitData) => {
    try {
      setLoading(true);
      await axios.post(`${API_BASE_URL}/api/units`, {
        ...unitData,
        module_id: moduleId,
        learning_objectives: unitData.learning_objectives.filter(obj => obj.trim() !== '')
      });
      setSuccess('Unit created successfully!');
      if (selectedProgram) {
        fetchProgramStructure(selectedProgram.id);
      }
    } catch (err) {
      setError('Failed to create unit');
    } finally {
      setLoading(false);
    }
  };

  const uploadContent = async (unitId, file) => {
    try {
      setLoading(true);
      const formData = new FormData();
      formData.append('file', file);
      
      await axios.post(`${API_BASE_URL}/api/units/${unitId}/content/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      setSuccess('Content uploaded successfully!');
      if (selectedProgram) {
        fetchProgramStructure(selectedProgram.id);
      }
    } catch (err) {
      setError('Failed to upload content');
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

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const DashboardView = () => (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Training Management Dashboard</h1>
        <p className="text-gray-600 mt-2">Transportation of Hazardous Materials Training Program Administration</p>
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
            <CardTitle className="text-lg">Modules</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {programStructure ? programStructure.modules.length : '-'}
            </div>
            <p className="text-sm text-gray-600">Learning modules</p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-orange-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">Units</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-600">
              {programStructure ? 
                programStructure.modules.reduce((total, module) => total + (module.units?.length || 0), 0) : '-'}
            </div>
            <p className="text-sm text-gray-600">Learning units</p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-purple-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">Content Items</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-purple-600">0</div>
            <p className="text-sm text-gray-600">Uploaded resources</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Recent Programs</CardTitle>
            <CardDescription>Latest training programs created</CardDescription>
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
                <p className="text-gray-500 text-center py-4">No programs created yet</p>
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
                onClick={() => setCurrentPage('programs')}
              >
                <GraduationCap className="h-4 w-4 mr-2" />
                Manage Programs
              </Button>
              <Button
                className="w-full justify-start"
                variant="outline"
                disabled
              >
                <Users className="h-4 w-4 mr-2" />
                Manage Learners (Coming Soon)
              </Button>
              <Button
                className="w-full justify-start"
                variant="outline"
                disabled
              >
                <Award className="h-4 w-4 mr-2" />
                View Certificates (Coming Soon)
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  const ProgramsView = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Programs Management</h1>
          <p className="text-gray-600 mt-2">Create and manage training programs</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Programs List */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Programs
                <Dialog>
                  <DialogTrigger asChild>
                    <Button size="sm">
                      <Plus className="h-4 w-4 mr-2" />
                      New Program
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                    <DialogHeader>
                      <DialogTitle>Create New Program</DialogTitle>
                      <DialogDescription>
                        Create a new training program with objectives and requirements.
                      </DialogDescription>
                    </DialogHeader>
                    
                    <form onSubmit={createProgram} className="space-y-4">
                      <div>
                        <Label htmlFor="title">Program Title</Label>
                        <Input
                          id="title"
                          value={programForm.title}
                          onChange={(e) => setProgramForm(prev => ({ ...prev, title: e.target.value }))}
                          placeholder="Enter program title"
                          required
                        />
                      </div>

                      <div>
                        <Label htmlFor="description">Description</Label>
                        <Textarea
                          id="description"
                          value={programForm.description}
                          onChange={(e) => setProgramForm(prev => ({ ...prev, description: e.target.value }))}
                          placeholder="Program description"
                          required
                        />
                      </div>

                      <div>
                        <Label>Learning Objectives</Label>
                        {programForm.learning_objectives.map((objective, index) => (
                          <div key={index} className="flex items-center gap-2 mt-2">
                            <Input
                              value={objective}
                              onChange={(e) => updateObjective(setProgramForm, index, e.target.value, programForm.learning_objectives)}
                              placeholder="Enter learning objective"
                            />
                            {programForm.learning_objectives.length > 1 && (
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={() => removeObjective(setProgramForm, index, programForm.learning_objectives)}
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
                          onClick={() => addObjectiveField(setProgramForm, programForm.learning_objectives)}
                          className="mt-2"
                        >
                          <Plus className="h-4 w-4 mr-2" />
                          Add Objective
                        </Button>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label htmlFor="expiry">Expiry Duration (months)</Label>
                          <Input
                            id="expiry"
                            type="number"
                            value={programForm.expiry_duration}
                            onChange={(e) => setProgramForm(prev => ({ ...prev, expiry_duration: parseInt(e.target.value) }))}
                            min="1"
                            required
                          />
                        </div>
                      </div>

                      <div>
                        <Label htmlFor="renewal">Renewal Requirements</Label>
                        <Textarea
                          id="renewal"
                          value={programForm.renewal_requirements}
                          onChange={(e) => setProgramForm(prev => ({ ...prev, renewal_requirements: e.target.value }))}
                          placeholder="Requirements for program renewal"
                        />
                      </div>

                      <div className="flex justify-end gap-2 pt-4">
                        <DialogTrigger asChild>
                          <Button type="button" variant="outline">Cancel</Button>
                        </DialogTrigger>
                        <Button type="submit" disabled={loading}>
                          {loading ? 'Creating...' : 'Create Program'}
                        </Button>
                      </div>
                    </form>
                  </DialogContent>
                </Dialog>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {programs.map((program) => (
                  <div
                    key={program.id}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedProgram?.id === program.id ? 'bg-blue-50 border-blue-200' : 'hover:bg-gray-50'
                    }`}
                    onClick={() => {
                      setSelectedProgram(program);
                      fetchProgramStructure(program.id);
                    }}
                  >
                    <h4 className="font-medium">{program.title}</h4>
                    <p className="text-sm text-gray-600">{program.description.substring(0, 80)}...</p>
                    <div className="flex gap-2 mt-2">
                      <Badge variant="secondary">{program.expiry_duration}mo expiry</Badge>
                    </div>
                  </div>
                ))}
                {programs.length === 0 && (
                  <p className="text-gray-500 text-center py-8">No programs created yet</p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Program Structure */}
        <div className="lg:col-span-2">
          {selectedProgram ? (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>{selectedProgram.title}</CardTitle>
                  <CardDescription>{selectedProgram.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium mb-2">Learning Objectives:</h4>
                      <ul className="list-disc list-inside space-y-1">
                        {selectedProgram.learning_objectives.map((objective, index) => (
                          <li key={index} className="text-sm text-gray-700">{objective}</li>
                        ))}
                      </ul>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium">Expiry Duration:</span>
                        <p>{selectedProgram.expiry_duration} months</p>
                      </div>
                      <div>
                        <span className="font-medium">Renewal Requirements:</span>
                        <p>{selectedProgram.renewal_requirements || 'None specified'}</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    Program Structure
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button size="sm">
                          <Plus className="h-4 w-4 mr-2" />
                          Add Module
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>Add New Module</DialogTitle>
                          <DialogDescription>
                            Create a new module for {selectedProgram.title}
                          </DialogDescription>
                        </DialogHeader>
                        
                        <form onSubmit={(e) => {
                          e.preventDefault();
                          createModule(selectedProgram.id, moduleForm);
                          setModuleForm({ title: '', description: '', order: 1 });
                        }} className="space-y-4">
                          <div>
                            <Label htmlFor="moduleTitle">Module Title</Label>
                            <Input
                              id="moduleTitle"
                              value={moduleForm.title}
                              onChange={(e) => setModuleForm(prev => ({ ...prev, title: e.target.value }))}
                              placeholder="Enter module title"
                              required
                            />
                          </div>

                          <div>
                            <Label htmlFor="moduleDescription">Description</Label>
                            <Textarea
                              id="moduleDescription"
                              value={moduleForm.description}
                              onChange={(e) => setModuleForm(prev => ({ ...prev, description: e.target.value }))}
                              placeholder="Module description"
                              required
                            />
                          </div>

                          <div>
                            <Label htmlFor="moduleOrder">Order</Label>
                            <Input
                              id="moduleOrder"
                              type="number"
                              value={moduleForm.order}
                              onChange={(e) => setModuleForm(prev => ({ ...prev, order: parseInt(e.target.value) }))}
                              min="1"
                              required
                            />
                          </div>

                          <div className="flex justify-end gap-2 pt-4">
                            <DialogTrigger asChild>
                              <Button type="button" variant="outline">Cancel</Button>
                            </DialogTrigger>
                            <Button type="submit" disabled={loading}>
                              {loading ? 'Creating...' : 'Create Module'}
                            </Button>
                          </div>
                        </form>
                      </DialogContent>
                    </Dialog>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {programStructure ? (
                    <div className="space-y-4">
                      {programStructure.modules.map((module) => (
                        <div key={module.id} className="border rounded-lg p-4">
                          <Collapsible
                            open={expandedModules.has(module.id)}
                            onOpenChange={() => toggleModuleExpansion(module.id)}
                          >
                            <CollapsibleTrigger className="flex items-center justify-between w-full">
                              <div className="flex items-center gap-2">
                                {expandedModules.has(module.id) ? 
                                  <ChevronDown className="h-4 w-4" /> : 
                                  <ChevronRight className="h-4 w-4" />
                                }
                                <h4 className="font-medium">{module.title}</h4>
                                <Badge variant="outline">Module {module.order}</Badge>
                              </div>
                              <Dialog>
                                <DialogTrigger asChild>
                                  <Button size="sm" variant="outline" onClick={(e) => e.stopPropagation()}>
                                    <Plus className="h-4 w-4 mr-2" />
                                    Add Unit
                                  </Button>
                                </DialogTrigger>
                                <DialogContent>
                                  <DialogHeader>
                                    <DialogTitle>Add New Unit</DialogTitle>
                                    <DialogDescription>
                                      Create a new unit for {module.title}
                                    </DialogDescription>
                                  </DialogHeader>
                                  
                                  <form onSubmit={(e) => {
                                    e.preventDefault();
                                    createUnit(module.id, unitForm);
                                    setUnitForm({ title: '', learning_objectives: [''], order: 1 });
                                  }} className="space-y-4">
                                    <div>
                                      <Label htmlFor="unitTitle">Unit Title</Label>
                                      <Input
                                        id="unitTitle"
                                        value={unitForm.title}
                                        onChange={(e) => setUnitForm(prev => ({ ...prev, title: e.target.value }))}
                                        placeholder="Enter unit title"
                                        required
                                      />
                                    </div>

                                    <div>
                                      <Label>Learning Objectives</Label>
                                      {unitForm.learning_objectives.map((objective, index) => (
                                        <div key={index} className="flex items-center gap-2 mt-2">
                                          <Input
                                            value={objective}
                                            onChange={(e) => updateObjective(setUnitForm, index, e.target.value, unitForm.learning_objectives)}
                                            placeholder="Enter learning objective"
                                          />
                                          {unitForm.learning_objectives.length > 1 && (
                                            <Button
                                              type="button"
                                              variant="outline"
                                              size="sm"
                                              onClick={() => removeObjective(setUnitForm, index, unitForm.learning_objectives)}
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
                                        onClick={() => addObjectiveField(setUnitForm, unitForm.learning_objectives)}
                                        className="mt-2"
                                      >
                                        <Plus className="h-4 w-4 mr-2" />
                                        Add Objective
                                      </Button>
                                    </div>

                                    <div>
                                      <Label htmlFor="unitOrder">Order</Label>
                                      <Input
                                        id="unitOrder"
                                        type="number"
                                        value={unitForm.order}
                                        onChange={(e) => setUnitForm(prev => ({ ...prev, order: parseInt(e.target.value) }))}
                                        min="1"
                                        required
                                      />
                                    </div>

                                    <div className="flex justify-end gap-2 pt-4">
                                      <DialogTrigger asChild>
                                        <Button type="button" variant="outline">Cancel</Button>
                                      </DialogTrigger>
                                      <Button type="submit" disabled={loading}>
                                        {loading ? 'Creating...' : 'Create Unit'}
                                      </Button>
                                    </div>
                                  </form>
                                </DialogContent>
                              </Dialog>
                            </CollapsibleTrigger>
                            
                            <CollapsibleContent className="mt-4">
                              <p className="text-sm text-gray-600 mb-4">{module.description}</p>
                              
                              {module.units && module.units.length > 0 ? (
                                <div className="space-y-3">
                                  {module.units.map((unit) => (
                                    <div key={unit.id} className="ml-6 p-3 bg-gray-50 rounded-lg">
                                      <div className="flex items-center justify-between">
                                        <div>
                                          <h5 className="font-medium">{unit.title}</h5>
                                          <Badge variant="secondary" className="mt-1">Unit {unit.order}</Badge>
                                        </div>
                                        <div className="flex gap-2">
                                          <Dialog>
                                            <DialogTrigger asChild>
                                              <Button size="sm" variant="outline">
                                                <Upload className="h-4 w-4 mr-2" />
                                                Upload Content
                                              </Button>
                                            </DialogTrigger>
                                            <DialogContent>
                                              <DialogHeader>
                                                <DialogTitle>Upload Content</DialogTitle>
                                                <DialogDescription>
                                                  Upload learning materials for {unit.title}
                                                </DialogDescription>
                                              </DialogHeader>
                                              
                                              <div className="space-y-4">
                                                <div>
                                                  <Label htmlFor="file">Select File</Label>
                                                  <Input
                                                    id="file"
                                                    type="file"
                                                    accept=".pdf,.docx,.doc,.mp4,.mp3,.jpg,.jpeg,.png,.gif"
                                                    onChange={(e) => {
                                                      if (e.target.files[0]) {
                                                        uploadContent(unit.id, e.target.files[0]);
                                                        e.target.value = '';
                                                      }
                                                    }}
                                                  />
                                                  <p className="text-sm text-gray-500 mt-1">
                                                    Supported formats: PDF, DOCX, MP4, MP3, JPG, PNG
                                                  </p>
                                                </div>
                                              </div>
                                            </DialogContent>
                                          </Dialog>
                                        </div>
                                      </div>
                                      
                                      {unit.learning_objectives && unit.learning_objectives.length > 0 && (
                                        <div className="mt-2">
                                          <p className="text-xs font-medium text-gray-700 mb-1">Objectives:</p>
                                          <ul className="text-xs text-gray-600 space-y-1">
                                            {unit.learning_objectives.map((objective, index) => (
                                              <li key={index}>• {objective}</li>
                                            ))}
                                          </ul>
                                        </div>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <p className="text-sm text-gray-500 ml-6">No units created yet</p>
                              )}
                            </CollapsibleContent>
                          </Collapsible>
                        </div>
                      ))}
                      
                      {programStructure.modules.length === 0 && (
                        <p className="text-gray-500 text-center py-8">No modules created yet. Create your first module to get started.</p>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <p className="text-gray-500">Loading program structure...</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="text-center py-12">
                <GraduationCap className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Select a Program</h3>
                <p className="text-gray-600">Choose a program from the list to view and manage its structure</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
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
                className="px-3 py-2 rounded-md text-sm font-medium text-gray-400 cursor-not-allowed"
                disabled
              >
                Learners
              </button>
              <button
                className="px-3 py-2 rounded-md text-sm font-medium text-gray-400 cursor-not-allowed"
                disabled
              >
                Assessments
              </button>
              <button
                className="px-3 py-2 rounded-md text-sm font-medium text-gray-400 cursor-not-allowed"
                disabled
              >
                Certificates
              </button>
              <button
                className="px-3 py-2 rounded-md text-sm font-medium text-gray-400 cursor-not-allowed"
                disabled
              >
                Reports
              </button>
            </nav>

            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm">
                <Settings className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="sm">
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
      </main>
    </div>
  );
}

export default App;