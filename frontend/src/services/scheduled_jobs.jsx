import api from "./api";

export const getScheduledJobs = async () => {
  const response = await api.get("/scheduled-jobs");
  return response.data;
};

export const createScheduledJob = async (jobData) => {
  const response = await api.post("/scheduled-jobs", jobData);
  return response.data;
};

export const deleteScheduledJob = async (id) => {
  const response = await api.delete(`/scheduled-jobs/${id}`);
  return response.data;
};