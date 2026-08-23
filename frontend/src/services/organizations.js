import api from "./api";

export const getOrganizations = async () => {
  const response = await api.get("/organizations");
  return response.data;
};

export const getOrganization = async (id) => {
  const response = await api.get(`/organizations/${id}`);
  return response.data;
};

export const createOrganization = async (data) => {
  const response = await api.post("/organizations", data);
  return response.data;
};