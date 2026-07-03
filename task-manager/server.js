require("dotenv").config();
const express = require("express");
const cors = require("cors");
const connectDB = require("./database/connection");
const authRoutes = require("./api/authRoutes");
const taskRoutes = require("./api/taskRoutes");

const app = express();

connectDB();

app.use(cors());
app.use(express.json());

app.use("/api/auth", authRoutes);
app.use("/api/tasks", taskRoutes);

app.get("/", (req, res) => {
  res.send("Smart Task Manager API is running");
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
