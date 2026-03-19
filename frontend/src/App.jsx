import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

import MainLayout from './layouts/MainLayout';
import Home from './pages/Home';
import Map from './pages/Map';
import Schedule from './pages/Schedule';
import Settings from './pages/Settings';
import DataInsights from './pages/DataInsights';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Home />} />
          <Route path="map" element={<Map />} />
          <Route path="schedule" element={<Schedule />} />
          <Route path="settings/*" element={<Settings />} />
          <Route path="data" element={<DataInsights />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App;
