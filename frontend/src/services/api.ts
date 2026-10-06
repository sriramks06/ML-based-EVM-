import axios from 'axios';
import type { Project, ProjectWeek, AnalysisResponse } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({ baseURL: API_URL });

export const fetchProjects = async (): Promise<Project[]> => {
  const res = await api.get<Project[]>('/projects');
  return res.data;
};

export const fetchProjectWeeks = async (projectId: number): Promise<ProjectWeek[]> => {
  const res = await api.get<ProjectWeek[]>(`/projects/${projectId}/weeks`);
  return res.data;
};

export const analyzeProject = async (projectId: number, week: number): Promise<AnalysisResponse> => {
  const res = await api.post<AnalysisResponse>('/analyze', { project_id: projectId, week });
  return res.data;
};

export const simulateProjectOutcome = async (projectId: number, week: number, overrides: Record<string, number>) => {
  const res = await api.post('/predict/simulate', {
    project_id: projectId,
    week,
    overrides
  });
  return res.data;
};
