import { useEffect, useState } from "react";
import {
  getOrganizations,
  createOrganization,
} from "../services/organizations";

const Organizations = () => {
  const [organizations, setOrganizations] = useState([]);
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(true);

  const loadOrganizations = async () => {
    try {
      const data = await getOrganizations();
      setOrganizations(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOrganizations();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();

    if (!name.trim()) return;

    try {
      await createOrganization({ name });
      setName("");
      await loadOrganizations();
    } catch (error) {
      console.error(error);
      alert(error.response?.data?.detail || "Failed to create organization");
    }
  };

  return (
    <div>
      <div className="page-title">
        <div>
          <h2>Organizations</h2>
          <p>Manage your organizations</p>
        </div>
      </div>

      <div className="create-card">
        <h3>Create Organization</h3>

        <form onSubmit={handleCreate} className="inline-form">
          <input
            type="text"
            placeholder="Organization name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />

          <button type="submit">Create</button>
        </form>
      </div>

      <div className="data-card">
        <h3>Organizations</h3>

        {loading ? (
          <p>Loading...</p>
        ) : organizations.length === 0 ? (
          <p>No organizations found.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Owner ID</th>
              </tr>
            </thead>

            <tbody>
              {organizations.map((org) => (
                <tr key={org.id}>
                  <td>{org.id}</td>
                  <td>{org.name}</td>
                  <td>{org.owner_id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default Organizations;