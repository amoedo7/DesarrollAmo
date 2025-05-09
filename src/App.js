import React from 'react';
import HeroSection from './components/HeroSection';
import ServicesSection from './components/ServicesSection';
import ProjectsSection from './components/ProjectsSection';
import AboutSection from './components/AboutSection';
import CtaSection from './components/CtaSection';

const App = () => {
  return (
    <div className="dark:bg-gray-900 transition-colors duration-300">
      <HeroSection />
      <ServicesSection />
      <ProjectsSection />
      <AboutSection />
      <CtaSection />
    </div>
  );
};

export default App;

// DONE