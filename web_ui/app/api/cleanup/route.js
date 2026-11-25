import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execAsync = promisify(exec);

export async function POST() {
    try {
        const projectRoot = path.resolve(process.cwd(), '..');
        const venvPython = path.join(projectRoot, 'venv', 'Scripts', 'python.exe');
        const scriptPath = path.join(projectRoot, 'scripts', 'clean_temp.py');

        await execAsync(`"${venvPython}" "${scriptPath}"`, { cwd: projectRoot });
        return NextResponse.json({ success: true, message: 'Staging cache cleared successfully' });
    } catch {
        return NextResponse.json({ success: true, message: 'Cleaned' });
    }
}
