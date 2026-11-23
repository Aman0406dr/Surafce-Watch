import mongoose from 'mongoose';

const findingSchema = new mongoose.Schema({
  severity: { type: String, required: true },
  category: { type: String, required: true },
  title: { type: String, required: true },
  detail: { type: String, required: true },
  recommendation: { type: String, required: true },
}, { _id: false });

export const scanSchema = new mongoose.Schema({
  target: { type: String, required: true, maxlength: 2048 },
  finalUrl: { type: String, required: true, maxlength: 2048 },
  host: { type: String, required: true, maxlength: 253 },
  scannedAt: { type: Date, required: true },
  durationMs: { type: Number, required: true },
  statusCode: { type: Number, required: true },
  contentType: { type: String, default: '' },
  pageTitle: { type: String, default: '' },
  redirects: { type: [String], default: [] },
  score: { type: Number, required: true, min: 0, max: 100 },
  findings: { type: [findingSchema], default: [] },
  summary: { type: mongoose.Schema.Types.Mixed, required: true },
  scopeNote: { type: String, required: true },
}, { timestamps: true });

export function getUserScanModel(userId) {
  const databaseName = `surface_user_${userId.toString()}`;
  const userDatabase = mongoose.connection.useDb(databaseName, { useCache: true });
  return userDatabase.models.Scan || userDatabase.model('Scan', scanSchema, 'scans');
}
