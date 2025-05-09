import React from 'react';

const services = [
  { icon: '🎨', title: 'Diseño de logos', description: 'Identidad visual única para tu marca' },
  { icon: '🖼️', title: 'Generación de imágenes', description: 'Creaciones visuales con IA a tu medida' },
  { icon: '🎧', title: 'Producción de audio', description: 'Voces, efectos y música generados por IA' },
  { icon: '🎥', title: 'Creación de videos', description: 'Contenido audiovisual personalizado' },
  { icon: '🚀', title: 'Landing pages', description: 'Sitios web efectivos y atractivos' },
  { icon: '💬', title: 'Chatbots inteligentes', description: 'Asistentes conversacionales para tu negocio' },
  { icon: '📊', title: 'Hojas de cálculo', description: 'Automatización y análisis de datos' },
  { icon: '⚙️', title: 'Automatizaciones', description: 'Flujos de trabajo con n8n y otras herramientas' },
];

const ServicesSection = () => {
  return (
    <section className="py-24 px-6 bg-gradient-to-br from-white to-blue-50 dark:from-gray-900 dark:to-gray-800">
      <div className="max-w-7xl mx-auto text-center">
        <h2 className="text-5xl font-extrabold mb-16 text-gray-800 dark:text-white tracking-tight">
          Lo que podemos <span className="text-pink-500">crear juntos</span>
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-10">
          {services.map((service, index) => (
            <div
              key={index}
              className="group relative bg-white/20 dark:bg-white/5 backdrop-blur-xl border border-gray-200 dark:border-gray-700 rounded-2xl p-6 text-left shadow-md transition-transform hover:-translate-y-2 hover:shadow-2xl duration-300"
            >
              <div className="text-5xl mb-4">{service.icon}</div>
              <h3 className="text-xl font-semibold mb-2 text-gray-900 dark:text-white">
                {service.title}
              </h3>
              <p className="text-gray-600 dark:text-gray-300 text-sm">
                {service.description}
              </p>
              <div className="absolute -top-1 -left-1 w-full h-full rounded-2xl bg-gradient-to-br from-pink-500/30 to-transparent blur-2xl opacity-0 group-hover:opacity-60 transition duration-500 -z-10" />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default ServicesSection;
