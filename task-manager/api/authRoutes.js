const express = require("express");
const jwt = require("jsonwebtoken");
const crypto = require("crypto");
const User = require("../database/User");
const { sendOTPEmail } = require("../database/emailService");

const router = express.Router();

function generateToken(id) {
  return jwt.sign({ id }, process.env.JWT_SECRET, { expiresIn: "30d" });
}

// POST /api/auth/register
router.post("/register", async (req, res) => {
  try {
    const { name, email, password } = req.body;

    if (!name || !email || !password) {
      return res.status(400).json({ message: "All fields are required" });
    }

    const existingUser = await User.findOne({ email });
    if (existingUser) {
      return res.status(400).json({ message: "Email already registered" });
    }

    const user = await User.create({ name, email, password });

    res.status(201).json({
      _id: user._id,
      name: user.name,
      email: user.email,
      token: generateToken(user._id)
    });
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
});

// POST /api/auth/login
router.post("/login", async (req, res) => {
  try {
    const { email, password } = req.body;
    const user = await User.findOne({ email });

    if (user && (await user.matchPassword(password))) {
      res.json({
        _id: user._id,
        name: user.name,
        email: user.email,
        token: generateToken(user._id)
      });
    } else {
      res.status(401).json({ message: "Invalid email or password" });
    }
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
});

module.exports = router;

// ===== FORGOT PASSWORD FLOW =====

// POST /api/auth/forgot-password - request an OTP by email
router.post("/forgot-password", async (req, res) => {
  try {
    const { email } = req.body;
    if (!email) return res.status(400).json({ message: "Email is required" });

    const user = await User.findOne({ email });

    // Always respond the same way whether or not the email exists -
    // this prevents attackers from using this endpoint to discover
    // which emails are registered.
    if (!user) {
      return res.json({ message: "If that email is registered, an OTP has been sent." });
    }

    // Generate a 6-digit OTP
    const otp = crypto.randomInt(100000, 999999).toString();

    user.resetOTP = otp;
    user.resetOTPExpires = Date.now() + 10 * 60 * 1000; // valid for 10 minutes
    await user.save();

    await sendOTPEmail(user.email, otp);

    res.json({ message: "If that email is registered, an OTP has been sent." });
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
});

// POST /api/auth/reset-password - verify OTP and set a new password
router.post("/reset-password", async (req, res) => {
  try {
    const { email, otp, newPassword } = req.body;

    if (!email || !otp || !newPassword) {
      return res.status(400).json({ message: "Email, OTP, and new password are all required" });
    }

    const user = await User.findOne({
      email,
      resetOTP: otp,
      resetOTPExpires: { $gt: Date.now() } // must not be expired
    });

    if (!user) {
      return res.status(400).json({ message: "Invalid or expired OTP" });
    }

    user.password = newPassword; // pre-save hook hashes it automatically
    user.resetOTP = undefined;
    user.resetOTPExpires = undefined;
    await user.save();

    res.json({ message: "Password reset successful. You can now log in." });
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
});
