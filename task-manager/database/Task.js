const mongoose = require("mongoose");

const taskSchema = new mongoose.Schema(
  {
    user: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true },
    text: { type: String, required: true },
    category: { type: String, default: "Personal" },
    priority: { type: String, enum: ["high", "medium", "low"], default: "medium" },
    dueDate: { type: String },
    completed: { type: Boolean, default: false }
  },
  { timestamps: true }
);

module.exports = mongoose.model("Task", taskSchema);
