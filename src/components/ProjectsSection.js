import React from 'react';

const projects = [
  { name: 'CriptAMO', description: 'Asesoría en criptomonedas para principiantes', accent: 'from-purple-500 to-indigo-500' },
  { name: 'PidAMO', description: 'Sistema de pedidos para restaurantes y bares', accent: 'from-green-500 to-emerald-500' },
  { name: 'ViajAMO', description: 'Planificador de viajes personalizado con IA', accent: 'from-blue-500 to-sky-500' },
  { name: 'TermAMO', description: 'Glosario técnico explicado de forma simple', accent: 'from-red-500 to-pink-500' },
  { name: 'TrucAMO', description: 'Tips tecnológicos para el día a día', accent: 'from-yellow-500 to-orange-500' },
];

const ProjectsSection = () => {
  return (
    <section className="py-24 px-6 bg-gradient-to-b from-white to-blue-50 dark:from-gray-900 dark:to-gray-800">
      <div className="max-w-7xl mx-auto text-center">
        <h2 className="text-5xl font-extrabold mb-16 text-gray-800 dark:text-white tracking-tight">
          Proyectos <span className="text-blue-600 dark:text-blue-300">destacados</span>
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-10">
          {projects.map((project, index) => (
            <div
              key={index}
              className="relative group p-6 rounded-2xl bg-white/20 dark:bg-white/5 border border-gray-200 dark:border-gray-700 backdrop-blur-xl shadow-md hover:shadow-2xl hover:-translate-y-2 transition-all duration-300"
            >
              <div className={`absolute inset-0 z-[-1] rounded-2xl opacity-0 group-hover:opacity-60 transition duration-500 blur-xl bg-gradient-to-br ${project.accent}`} />
              
              <h3 className="text-2xl font-bold mb-3 text-gray-900 dark:text-white">{project.name}</h3>
              <p className="text-gray-700 dark:text-gray-300 text-sm">{project.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default ProjectsSection;
