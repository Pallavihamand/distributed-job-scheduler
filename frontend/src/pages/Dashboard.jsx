
import { useEffect, useState } from "react";

import { getOrganizations } from "../services/organizations";
import { getProjects } from "../services/projects";
import { getQueues } from "../services/queues";
import { getJobs } from "../services/jobs";
import { getWorkers } from "../services/workers";

const Dashboard = () => {
  const [stats, setStats] = useState({
    organizations: 0,
    projects: 0,
    queues: 0,
    jobs: 0,
    workers: 0,
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadStats = async () => {
      try {
        const [
          organizations,
          projects,
          queues,
          jobs,
          workers,
        ] = await Promise.all([
          getOrganizations(),
          getProjects(),
          getQueues(),
          getJobs(),
          getWorkers(),
        ]);

        setStats({
          organizations: Array.isArray(organizations)
            ? organizations.length
            : 0,

          projects: Array.isArray(projects)
            ? projects.length
            : 0,

          queues: Array.isArray(queues)
            ? queues.length
            : 0,

          jobs: Array.isArray(jobs)
            ? jobs.length
            : 0,

          workers: Array.isArray(workers)
            ? workers.length
            : 0,
        });
      } catch (error) {
        console.error("Failed to load dashboard:", error);
      } finally {
        setLoading(false);
      }
    };

    loadStats();
  }, []);

  const cards = [
    {
      title: "Organizations",
      value: stats.organizations,
      icon: "▣",
    },
    {
      title: "Projects",
      value: stats.projects,
      icon: "◫",
    },
    {
      title: "Queues",
      value: stats.queues,
      icon: "☷",
    },
    {
      title: "Jobs",
      value: stats.jobs,
      icon: "⚙",
    },
    {
      title: "Workers",
      value: stats.workers,
      icon: "◉",
    },
  ];

  return (
    <div>
      <div className="page-title">
        <h2>Dashboard</h2>
        <p>
          Overview of your distributed job scheduler
        </p>
      </div>

      <div className="stats-grid">
        {cards.map((card) => (
          <div
            className="stat-card"
            key={card.title}
          >
            <div className="stat-header">
              <span className="stat-title">
                {card.title}
              </span>

              <span className="stat-icon">
                {card.icon}
              </span>
            </div>

            <div className="stat-value">
              {loading ? "..." : card.value}
            </div>

            <div className="stat-footer">
              <span>Live data</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Dashboard;

