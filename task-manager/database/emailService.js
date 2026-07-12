const nodemailer = require("nodemailer");

// Uses Gmail SMTP by default - free, no credit card needed.
// Requires an "App Password" (not your normal Gmail password) - see README.
const transporter = nodemailer.createTransport({
  service: "gmail",
  auth: {
    user: process.env.EMAIL_USER,
    pass: process.env.EMAIL_PASS
  }
});

async function sendOTPEmail(toEmail, otp) {
  await transporter.sendMail({
    from: `"Smart Task Manager" <${process.env.EMAIL_USER}>`,
    to: toEmail,
    subject: "Your Password Reset OTP",
    html: `
      <div style="font-family:Arial,sans-serif;max-width:400px;margin:auto;">
        <h2>Password Reset Request</h2>
        <p>Use the OTP below to reset your password. It is valid for 10 minutes.</p>
        <h1 style="letter-spacing:5px;">${otp}</h1>
        <p>If you did not request this, you can safely ignore this email.</p>
      </div>
    `
  });
}

module.exports = { sendOTPEmail };
