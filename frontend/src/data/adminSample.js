// SAMPLE DATA for the admin dashboard. Replace with API data when /api/admin/* is ready.

export const sampleKpis = {
  totalChecks: 2348,
  highRisk: 742,
  totalRwf: 1400000000,
  activePatterns: 12,
};

// Approximate centre of each Kigali sector, with a sample report count.
export const sampleHeatmap = [
  { sector: "Kimironko", lat: -1.9441, lng: 30.1269, reports: 46 },
  { sector: "Nyarugenge", lat: -1.9536, lng: 30.0605, reports: 38 },
  { sector: "Kicukiro", lat: -1.9706, lng: 30.1044, reports: 21 },
  { sector: "Remera", lat: -1.9574, lng: 30.1126, reports: 17 },
];

export const sampleModus = [
  { label: "Visa fees", value: 40 },
  { label: "Fake scholarships", value: 35 },
  { label: "Fake job offers", value: 25 },
];

// Domains only, never personal email addresses.
export const sampleDomains = [
  { domain: "sample-visa-offers.example", count: 127, firstSeen: "2026-10-05", risk: "high", status: "open" },
  { domain: "sample-job-agency.example", count: 64, firstSeen: "2026-10-18", risk: "high", status: "reviewing" },
  { domain: "sample-scholarship.example", count: 19, firstSeen: "2026-10-27", risk: "medium", status: "open" },
];
