
import { useState } from "react";

const ScheduledJobs = () => {
  const [showForm, setShowForm] = useState(false);

  const [job, setJob] = useState({
    name: "",
    queue: "default",
    type: "scheduled",
    scheduledTime: "",
    cron: "",
  });

  const handleChange = (e) => {
    setJob({
      ...job,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    console.log("Scheduled Job:", job);

    alert("Scheduled job created successfully");

    setJob({
      name: "",
      queue: "default",
      type: "scheduled",
      scheduledTime: "",
      cron: "",
    });

    setShowForm(false);
  };

  return (
    <div>

      {/* PAGE HEADER */}
      <div className="page-title">

        <div>
          <h2>Scheduled Jobs</h2>

          <p>
            Manage delayed, scheduled and recurring jobs
          </p>
        </div>

        <button
          className="primary-button"
          onClick={() => setShowForm(!showForm)}
        >
          + Create Scheduled Job
        </button>

      </div>


      {/* CREATE FORM */}
      {showForm && (
        <div className="page-card">

          <h3>Create Scheduled Job</h3>

          <form onSubmit={handleSubmit}>

            <div className="form-grid">

              <div className="form-group">
                <label>Job Name</label>

                <input
                  type="text"
                  name="name"
                  value={job.name}
                  onChange={handleChange}
                  placeholder="Example: Send Report"
                  required
                />
              </div>


              <div className="form-group">
                <label>Queue</label>

                <select
                  name="queue"
                  value={job.queue}
                  onChange={handleChange}
                >
                  <option value="default">
                    default
                  </option>

                  <option value="high-priority">
                    high-priority
                  </option>

                  <option value="low-priority">
                    low-priority
                  </option>
                </select>
              </div>


              <div className="form-group">
                <label>Job Type</label>

                <select
                  name="type"
                  value={job.type}
                  onChange={handleChange}
                >
                  <option value="scheduled">
                    Scheduled
                  </option>

                  <option value="recurring">
                    Recurring
                  </option>

                  <option value="delayed">
                    Delayed
                  </option>
                </select>
              </div>


              {job.type !== "recurring" && (
                <div className="form-group">
                  <label>Scheduled Time</label>

                  <input
                    type="datetime-local"
                    name="scheduledTime"
                    value={job.scheduledTime}
                    onChange={handleChange}
                    required
                  />
                </div>
              )}


              {job.type === "recurring" && (
                <div className="form-group">
                  <label>Cron Expression</label>

                  <input
                    type="text"
                    name="cron"
                    value={job.cron}
                    onChange={handleChange}
                    placeholder="0 9 * * *"
                    required
                  />

                  <small>
                    Example: 0 9 * * * = every day at 9 AM
                  </small>
                </div>
              )}

            </div>


            <div className="form-actions">

              <button
                type="button"
                className="secondary-button"
                onClick={() => setShowForm(false)}
              >
                Cancel
              </button>

              <button
                type="submit"
                className="primary-button"
              >
                Create Job
              </button>

            </div>

          </form>

        </div>
      )}


      {/* SCHEDULED JOB LIST */}
      <div className="page-card">

        <div className="card-header">

          <div>
            <h3>Scheduled Jobs</h3>

            <p>
              Upcoming and recurring jobs
            </p>
          </div>

        </div>


        <div className="empty-state">

          <div className="empty-icon">
            ◷
          </div>

          <h3>
            No scheduled jobs yet
          </h3>

          <p>
            Create a scheduled, delayed or recurring job
            to see it here.
          </p>

        </div>

      </div>

    </div>
  );
};

export default ScheduledJobs;

