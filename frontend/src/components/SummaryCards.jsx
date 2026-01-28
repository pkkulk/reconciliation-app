import React from 'react';
import { motion } from 'framer-motion';
import { Layers, Database, CheckCheck, AlertTriangle, FileMinus, SearchX, ArrowRight } from 'lucide-react';
export default function SummaryCards({ summary }) {
    if (!summary) return null;
    const cards = [
        { label: "Total Statement", value: summary.total_statement, icon: Layers, color: "bg-blue-500", textColor: "text-blue-500" },
        { label: "Total Settlement", value: summary.total_settlement, icon: Database, color: "bg-purple-500", textColor: "text-purple-500" },
        { label: "Matched", value: summary.matched, icon: CheckCheck, color: "bg-emerald-500", textColor: "text-emerald-600", highlight: true },
        { label: "Variance", value: summary.variance, icon: AlertTriangle, color: "bg-amber-500", textColor: "text-amber-600" },
        { label: "Statement Only", value: summary.only_in_statement, icon: FileMinus, color: "bg-slate-400", textColor: "text-slate-600" },
        { label: "Settlement Only", value: summary.only_in_settlement, icon: FileMinus, color: "bg-slate-400", textColor: "text-slate-600" },
        { label: "Mismatch", value: summary.reversal_mismatch_rows, icon: SearchX, color: "bg-rose-500", textColor: "text-rose-600" },
    ];
    const container = {
        hidden: { opacity: 0 },
        show: {
            opacity: 1,
            transition: {
                staggerChildren: 0.1
            }
        }
    };
    const item = {
        hidden: { opacity: 0, y: 20 },
        show: { opacity: 1, y: 0 }
    };
    return (
        <motion.div
            variants={container}
            initial="hidden"
            animate="show"
            className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4"
        >
            {cards.map((card, idx) => {
                const Icon = card.icon;
                return (
                    <motion.div
                        key={idx}
                        variants={item}
                        className={`relative overflow-hidden bg-white rounded-2xl p-4 shadow-sm border border-slate-100 hover:shadow-md transition-shadow duration-300 ${card.highlight ? 'ring-1 ring-emerald-100' : ''}`}
                    >
                        <div className="flex flex-col h-full justify-between space-y-3">
                            <div className="flex items-center justify-between">
                                <div className={`p-2 rounded-lg ${card.color} bg-opacity-10`}>
                                    <Icon className={`w-5 h-5 ${card.textColor}`} />
                                </div>
                                {}
                            </div>
                            <div>
                                <h4 className="text-2xl font-bold text-slate-900 tracking-tight">{card.value.toLocaleString()}</h4>
                                <p className="text-xs font-medium text-slate-500 truncate mt-1">{card.label}</p>
                            </div>
                        </div>
                        {}
                        <div className={`absolute -right-4 -bottom-4 opacity-5 pointer-events-none`}>
                            <Icon className={`w-24 h-24 ${card.textColor}`} />
                        </div>
                    </motion.div>
                );
            })}
        </motion.div>
    );
}
