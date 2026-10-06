import React from 'react';

interface SectionCardProps {
  title: string;
  children: React.ReactNode;
  className?: string;
  icon?: React.ReactNode;
}

export const SectionCard: React.FC<SectionCardProps> = ({ title, children, className, icon }) => (
  <div className={`section-card ${className ?? ''}`}>
    <div className="section-card-title">
      {icon && <span className="section-icon">{icon}</span>}
      {title}
    </div>
    <div className="section-card-body">{children}</div>
  </div>
);
