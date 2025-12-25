"use client";
import React, { createContext, useContext, useState, ReactNode } from 'react';

export interface CallEntry {
  id: string;
  name: string;
  phone: string;
  notes?: string;
  description?: string;
  status?: 'pending' | 'calling' | 'completed';
}

interface CallingListContextType {
  entries: CallEntry[];
  addEntry: (entry: Omit<CallEntry, 'id' | 'status'>) => void;
  addMultipleEntries: (entries: Omit<CallEntry, 'id' | 'status'>[]) => void;
  updateEntry: (id: string, updates: Partial<CallEntry>) => void;
  deleteEntry: (id: string) => void;
  reorderEntries: (newOrder: CallEntry[]) => void;
}

const CallingListContext = createContext<CallingListContextType | undefined>(undefined);

export function CallingListProvider({ children }: { children: ReactNode }) {
  const [entries, setEntries] = useState<CallEntry[]>([
    { id: '1', name: 'Rajesh Kumar', phone: '+91 98765 43210', notes: 'Regarding water supply issue', description: 'Inquiry about water supply', status: 'pending' },
    { id: '2', name: 'Priya Sharma', phone: '+91 98765 43211', notes: 'Complaint about road maintenance', description: 'Road maintenance complaint', status: 'pending' },
    { id: '3', name: 'Amit Patel', phone: '+91 98765 43212', description: 'License application status', status: 'pending' },
    { id: '4', name: 'Sneha Gupta', phone: '+91 98765 43213', description: 'Tax payment query', status: 'pending' },
    { id: '5', name: 'Vikram Singh', phone: '+91 98765 43214', description: '', status: 'pending' },
  ]);

  const addEntry = (entry: Omit<CallEntry, 'id' | 'status'>) => {
    const newEntry: CallEntry = {
      ...entry,
      id: Date.now().toString(),
      status: 'pending',
      // Ensure both notes and description are synced
      notes: entry.notes || entry.description || '',
      description: entry.description || entry.notes || ''
    };
    setEntries(prev => [newEntry, ...prev]);
  };

  const addMultipleEntries = (newEntries: Omit<CallEntry, 'id' | 'status'>[]) => {
    const formattedEntries: CallEntry[] = newEntries.map(entry => ({
      ...entry,
      id: `${Date.now()}-${Math.random()}`,
      status: 'pending' as const,
      notes: entry.notes || entry.description || '',
      description: entry.description || entry.notes || ''
    }));
    setEntries(prev => [...formattedEntries, ...prev]);
  };

  const updateEntry = (id: string, updates: Partial<CallEntry>) => {
    setEntries(prev => prev.map(entry => {
      if (entry.id === id) {
        const updated = { ...entry, ...updates };
        // Keep notes and description in sync
        if (updates.description !== undefined) {
          updated.notes = updates.description;
        }
        if (updates.notes !== undefined) {
          updated.description = updates.notes;
        }
        return updated;
      }
      return entry;
    }));
  };

  const deleteEntry = (id: string) => {
    setEntries(prev => prev.filter(entry => entry.id !== id));
  };

  const reorderEntries = (newOrder: CallEntry[]) => {
    setEntries(newOrder);
  };

  return (
    <CallingListContext.Provider
      value={{
        entries,
        addEntry,
        addMultipleEntries,
        updateEntry,
        deleteEntry,
        reorderEntries
      }}
    >
      {children}
    </CallingListContext.Provider>
  );
}

export function useCallingList() {
  const context = useContext(CallingListContext);
  if (context === undefined) {
    throw new Error('useCallingList must be used within a CallingListProvider');
  }
  return context;
}