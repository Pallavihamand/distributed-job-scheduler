import { useEffect, useState } from "react";
import { getWorkers } from "../services/workers";

const Workers = () => {
  const [workers, setWorkers] = useState([]);

  useEffect(() => {
    const loadWorkers = async () => {
      try {
        const data = await getWorkers();
        setWorkers(data);
      } catch (error) {
        console.error(error);
      }
    };

    loadWorkers();
  }, []);

  return (
    <div>
      <div className="page-title">
        <h2>Workers</h2>
        <p>Monitor distributed job workers</p>
      </div>

      <div className="data-card">
        <h3>Registered Workers</h3>

        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Status</th>
            </tr>
          </thead>

          <tbody>
            {workers.map((worker) => (
              <tr key={worker.id}>
                <td>{worker.id}</td>
                <td>{worker.name || "-"}</td>
                <td>
                  <span className="status">
                    {worker.status || "unknown"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {workers.length === 0 && (
          <p>No workers registered.</p>
        )}
      </div>
    </div>
  );
};

export default Workers;