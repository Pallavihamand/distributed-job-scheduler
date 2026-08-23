import api from "./api";

export const getQueues = async () => {
  const response = await api.get("/queues");
  return response.data;
};

export const getQueue = async (id) => {
  const response = await api.get(`/queues/${id}`);
  return response.data;
};

export const createQueue = async (data) => {
  const response = await api.post("/queues", data);
  return response.data;
};

export const updateQueue = async (id, data) => {
  const response = await api.put(`/queues/${id}`, data);
  return response.data;
};

export const deleteQueue = async (id) => {
  const response = await api.delete(`/queues/${id}`);
  return response.data;
};