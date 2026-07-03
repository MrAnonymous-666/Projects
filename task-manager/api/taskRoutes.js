const express = require("express");
const Task = require("../database/Task");
const protect = require("../middleware/authMiddleware");

const router = express.Router();

// All task routes require a valid login
router.use(protect);

// GET /api/tasks - get all tasks for the logged-in user
router.get("/", async (req, res) => {
  const tasks = await Task.find({ user: req.user._id }).sort({ createdAt: -1 });
  res.json(tasks);
});

// POST /api/tasks - create a task
router.post("/", async (req, res) => {
  try {
    const { text, category, priority, dueDate } = req.body;
    if (!text) return res.status(400).json({ message: "Task text is required" });

    const task = await Task.create({
      user: req.user._id,
      text,
      category,
      priority,
      dueDate
    });

    res.status(201).json(task);
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
});

// PUT /api/tasks/:id - update a task (edit text, toggle complete, etc)
router.put("/:id", async (req, res) => {
  const task = await Task.findOne({ _id: req.params.id, user: req.user._id });
  if (!task) return res.status(404).json({ message: "Task not found" });

  Object.assign(task, req.body);
  const updated = await task.save();
  res.json(updated);
});

// DELETE /api/tasks/:id
router.delete("/:id", async (req, res) => {
  const task = await Task.findOneAndDelete({ _id: req.params.id, user: req.user._id });
  if (!task) return res.status(404).json({ message: "Task not found" });
  res.json({ message: "Task deleted" });
});

module.exports = router;
