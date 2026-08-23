import api from "./api";

export const getWorkers = async () => {
  const response = await api.get("/workers");
  return response.data;
};

export const getWorker = async (id) => {
  const response = await api.get(`/workers/${id}`);
  return response.data;
};

export const createWorker = async (data) => {
  const response = await api.post("/workers", data);
  return response.data;
};