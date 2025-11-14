import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import App from './ui/App';
import ObjectiveComparisonEnhanced from './components/ObjectiveComparisonEnhanced';
import Advanced3DPage from './ui/Advanced3DPage';
import MarketingROIPage from './ui/MarketingROIPage';
import DAGVisualizationPage from './ui/DAGVisualizationPage';
import DAGComprehensivePage from './ui/DAGComprehensivePage';

createRoot(document.getElementById('root')!).render(
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<App />} />
      <Route path="/objective-comparison" element={<ObjectiveComparisonEnhanced />} />
      <Route path="/advanced-3d" element={<Advanced3DPage />} />
      <Route path="/marketing-roi" element={<MarketingROIPage />} />
      <Route path="/dag-visualization" element={<DAGVisualizationPage />} />
      <Route path="/dag-comprehensive" element={<DAGComprehensivePage />} />
    </Routes>
  </BrowserRouter>
);
