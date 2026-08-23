import { useEffect, useState } from "react";
import {
  getJobs,
  createJob,
  deleteJob,
} from "../services/jobs";

const Jobs = () => {
  const [jobs, setJobs] = useState([]);

  const [form, setForm] = useState({
    queue_id: "",
    job_type: "",
    payload: '{"message":"Hello Worker"}',
  });

  const loadJobs = async () => {
    try {
      const data = await getJobs();
      setJobs(data);
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    loadJobs();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();

    try {
      const parsedPayload = JSON.parse(form.payload);

      await createJob({
        queue_id: Number(form.queue_id),
        job_type: form.job_type,
        payload: parsedPayload,
      });

      setForm({
        queue_id: "",
        job_type: "",
        payload: '{"message":"Hello Worker"}',
      });

      await loadJobs();
    } catch (error) {
      if (error instanceof SyntaxError) {
        alert("Payload must contain valid JSON.");
        return;
      }

      alert(
        error.response?.data?.detail ||
          "Failed to create job"
      );
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this job?")) return;

    try {
      await deleteJob(id);
      await loadJobs();
    }  catch {
  alert("Failed to delete job");
}
  };

  return (
    <div>
      <div className="page-title">
        <h2>Jobs</h2>
        <p>Create and monitor background jobs</p>
      </div>

      <div className="create-card">
        <h3>Create Job</h3>

        <form onSubmit={handleCreate}>
          <label>Queue ID</label>

          <input
            type="number"
            value={form.queue_id}
            onChange={(e) =>
              setForm({
                ...form,
                queue_id: e.target.value,
              })
            }
            required
          />

          <label>Job Type</label>

          <input
            value={form.job_type}
            onChange={(e) =>
              setForm({
                ...form,
                job_type: e.target.value,
              })
            }
            placeholder="email"
            required
          />

          <label>Payload JSON</label>

          <textarea
            rows="5"
            value={form.payload}
            onChange={(e) =>
              setForm({
                ...form,
                payload: e.target.value,
              })
            }
            required
          />

          <button type="submit">Create Job</button>
        </form>
      </div>

      <div className="data-card">
        <h3>Jobs</h3>

        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Queue</th>
              <th>Type</th>
              <th>Status</th>
              <th>Attempts</th>
              <th>Action</th>
            </tr>
          </thead>

          <tbody>
            {jobs.map((job) => (
              <tr key={job.id}>
                <td>{job.id}</td>
                <td>{job.queue_id}</td>
                <td>{job.job_type}</td>
                <td>
                  <span className={`status ${job.status}`}>
                    {job.status}
                  </span>
                </td>
                <td>{job.attempts}</td>

                <td>
                  <button
                    className="delete-btn"
                    onClick={() => handleDelete(job.id)}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Jobs;