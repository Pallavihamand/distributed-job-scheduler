import api from "./api";

export const getJobs = async () => {
  const response = await api.get("/jobs");
  return response.data;
};

export const getJob = async (id) => {
  const response = await api.get(`/jobs/${id}`);
  return response.data;
};

export const createJob = async (data) => {
  const response = await api.post("/jobs", data);
  return response.data;
};

export const createBatchJobs = async (data) => {
  const response = await api.post("/jobs/batch", data);
  return response.data;
};

export const deleteJob = async (id) => {
  const response = await api.delete(`/jobs/${id}`);
  return response.data;
};