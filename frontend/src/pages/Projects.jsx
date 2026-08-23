import { useEffect, useState } from "react";
import {
  getProjects,
  createProject,
} from "../services/projects";

import { getOrganizations } from "../services/organizations";

const Projects = () => {
  const [projects, setProjects] = useState([]);
  const [organizations, setOrganizations] = useState([]);

  const [organizationId, setOrganizationId] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const loadData = async () => {
    try {
      const [projectData, organizationData] = await Promise.all([
        getProjects(),
        getOrganizations(),
      ]);

      setProjects(projectData);
      setOrganizations(organizationData);

      if (organizationData.length > 0) {
        setOrganizationId(organizationData[0].id);
      }
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();

    try {
      await createProject({
        organization_id: Number(organizationId),
        name,
        description: description || null,
      });

      setName("");
      setDescription("");

      await loadData();
    } catch (error) {
      console.error(error);

      alert(
        error.response?.data?.detail ||
          "Failed to create project"
      );
    }
  };

  return (
    <div>
      <div className="page-title">
        <h2>Projects</h2>
        <p>Manage projects inside your organizations</p>
      </div>

      <div className="create-card">
        <h3>Create Project</h3>

        <form onSubmit={handleCreate}>
          <label>Organization</label>

          <select
            value={organizationId}
            onChange={(e) => setOrganizationId(e.target.value)}
            required
          >
            {organizations.map((org) => (
              <option key={org.id} value={org.id}>
                {org.name} (ID: {org.id})
              </option>
            ))}
          </select>

          <label>Project Name</label>

          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="My Project"
            required
          />

          <label>Description</label>

          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Project description"
          />

          <button type="submit">Create Project</button>
        </form>
      </div>

      <div className="data-card">
        <h3>Projects</h3>

        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Organization</th>
              <th>Description</th>
            </tr>
          </thead>

          <tbody>
            {projects.map((project) => (
              <tr key={project.id}>
                <td>{project.id}</td>

                <td>{project.name}</td>

                <td>{project.organization_id}</td>

                <td>{project.description || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Projects;