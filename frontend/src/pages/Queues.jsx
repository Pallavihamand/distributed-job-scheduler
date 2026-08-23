import { useEffect, useState } from "react";
import {
  getQueues,
  createQueue,
} from "../services/queues";

const Queues = () => {
  const [queues, setQueues] = useState([]);

  const [form, setForm] = useState({
    project_id: "",
    name: "",
  });

  const loadQueues = async () => {
    try {
      const data = await getQueues();
      setQueues(data);
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    loadQueues();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();

    try {
      await createQueue({
        project_id: Number(form.project_id),
        name: form.name,
      });

      setForm({
        project_id: "",
        name: "",
      });

      await loadQueues();
    } catch (error) {
      alert(error.response?.data?.detail || "Failed to create queue");
    }
  };

  return (
    <div>
      <div className="page-title">
        <h2>Queues</h2>
        <p>Manage job queues</p>
      </div>

      <div className="create-card">
        <h3>Create Queue</h3>

        <form onSubmit={handleCreate}>
          <label>Project ID</label>

          <input
            type="number"
            value={form.project_id}
            onChange={(e) =>
              setForm({
                ...form,
                project_id: e.target.value,
              })
            }
            required
          />

          <label>Queue Name</label>

          <input
            value={form.name}
            onChange={(e) =>
              setForm({
                ...form,
                name: e.target.value,
              })
            }
            placeholder="default"
            required
          />

          <button type="submit">Create Queue</button>
        </form>
      </div>

      <div className="data-card">
        <h3>Queues</h3>

        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Project ID</th>
            </tr>
          </thead>

          <tbody>
            {queues.map((queue) => (
              <tr key={queue.id}>
                <td>{queue.id}</td>
                <td>{queue.name}</td>
                <td>{queue.project_id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Queues;