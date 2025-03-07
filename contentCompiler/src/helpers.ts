import path from "path";
import * as fs from "fs";
import { SimpleGit } from "simple-git";
import { Probot, Context } from "probot";


// Helper function to check if the commit is from our app
export function isAppCommit(context: Context<'push'>) {
    const sender = context.payload.sender;
    const commits = context.payload.commits || [];
    
    // Check both the sender and the commit message
    return (sender && sender.type === 'Bot' && sender.login.endsWith('[bot]')) ||
           commits.some(commit => commit.message.includes('[bot-commit]'));
}

// Helper function to get default configuration values
export function getDefaultConfig(context: Context<any>) {
    const gitAppName = process.env.GITHUB_APP_NAME || '';
    const gitAppEmail = process.env.GITHUB_APP_EMAIL || '';

    const payload = context.payload;
    const repoOwner = payload.repository.owner.login;
    const repoName = payload.repository.name;
    const repoUrl = payload.repository.clone_url;  

    const datasetRepoUrl = process.env.DATASET_REPO_URL || '';
    const clonedRepoFolder = process.env.CLONE_REPO_FOLDER || 'src/cloned_repo';
    const tempStorageFolder = process.env.TEMP_STORAGE_FOLDER || 'src/temp_storage';
    const datasetFolder = process.env.DATASET_FOLDER || 'src/dataset';
    const reportFiles = process.env.REPORT_FILES?.split(',') || [];

    const __dirname = process.cwd();
    const cloneTargetDirectory = path.join(__dirname, clonedRepoFolder);
    const cloneBuildDirectory = path.join(cloneTargetDirectory, 'build');

    const sourceBuildDirectory = path.join(__dirname, clonedRepoFolder, 'build');
    const tempDestinationBuildDir = path.join(__dirname, tempStorageFolder, 'build');
    const tempStorageDirectory = path.join(__dirname, tempStorageFolder);

    return { gitAppName, gitAppEmail, repoOwner, repoName, repoUrl, clonedRepoFolder, reportFiles, cloneTargetDirectory, cloneBuildDirectory, sourceBuildDirectory, tempDestinationBuildDir, tempStorageDirectory, datasetRepoUrl, datasetFolder };
}

// Helper function to get the installation token
export const getInstallationToken = async (app: Probot, context: Context<any>) => {
    const octokit = await app.auth();
    const installationId = context.payload.installation?.id;
    if (!installationId) {
        throw new Error('No installation ID found');
    }
    const { token } = await octokit.auth({
        type: 'installation',
        installationId
    }) as { token: string };

    return token;
}

// Helper function to clear temp storage
export function clearTempStorage(cloneTargetDirectory: string, tempStorageDirectory: string, app: Probot, context: Context<any>) {
    try {
        // Remove the cloned_repo folder if it exists
        if (fs.existsSync(cloneTargetDirectory)) {
            deleteFolderRecursiveSync(app, cloneTargetDirectory);
        }
        fs.mkdirSync(cloneTargetDirectory);
        // Remove the cloned_repo folder if it exists
        if (fs.existsSync(tempStorageDirectory)) {
            deleteFolderRecursiveSync(app, tempStorageDirectory);
        }
        fs.mkdirSync(tempStorageDirectory);
    } catch (error: any) {
        context.log.error(`Failed to remove temp folders: ${error.message}`);
        throw error;
    }
}

// Helper function to configure git
export const configureGit = async (git: SimpleGit, gitAppName: string, gitAppEmail: string) => {
    if (!gitAppName || !gitAppEmail) {
        throw new Error('Git app name or email not configured in environment variables');
    }
    await git.addConfig("user.name", gitAppName, false, 'local');
    await git.addConfig("user.email", gitAppEmail, false, 'local');
    // Set committer info explicitly
    await git.addConfig("committer.name", gitAppName, false, 'local');
    await git.addConfig("committer.email", gitAppEmail, false, 'local');
}

// Helper function to delete a folder recursively
export const deleteFolderRecursiveSync = (app: Probot, folderPath: string) => {
    if (fs.existsSync(folderPath)) {
        const files = fs.readdirSync(folderPath);

        files.forEach((file) => {
            const currentPath = path.join(folderPath, file);

            if (fs.statSync(currentPath).isDirectory()) {
                deleteFolderRecursiveSync(app,currentPath);
            } else {
                fs.unlinkSync(currentPath);
            }
        });

        fs.rmdirSync(folderPath);
    } else {
        app.log.warn(`Folder ${folderPath} does not exist`);
    }
}
